#!/usr/bin/env python3
"""
Robust Enhanced System - Rate Limit Handling
===========================================

Version with automatic retry logic and rate limit handling for Azure OpenAI.
"""

import asyncio
import argparse
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Import enhanced agents with adaptive processing
from src.enhanced_agents import fast, meeting_fast, adaptive_segment_content


class RateLimitHandler:
    """Handle rate limiting and retries for Azure OpenAI."""
    
    def __init__(self, max_retries: int = 3, base_delay: int = 60):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.retry_count = 0
    
    async def execute_with_retry(self, operation, *args, **kwargs):
        """Execute operation with automatic retry on rate limits."""
        
        for attempt in range(self.max_retries + 1):
            try:
                self.retry_count = attempt
                result = await operation(*args, **kwargs)
                
                if attempt > 0:
                    print(f"✅ Recovered after {attempt} retries")
                
                return result
                
            except Exception as e:
                error_str = str(e)
                
                # Check for rate limit errors (including fast-agent specific)
                is_rate_limit = (
                    "429" in error_str or 
                    "rate limit" in error_str.lower() or
                    "Failed to parse plan: Error code: 429" in error_str or
                    "token rate limit" in error_str.lower() or
                    "exceeded token rate limit" in error_str.lower()
                )
                
                if is_rate_limit:
                    if attempt < self.max_retries:
                        # Calculate delay with exponential backoff
                        delay = self.base_delay * (2 ** attempt)
                        
                        print(f"🚨 Rate limit hit (attempt {attempt + 1}/{self.max_retries + 1})")
                        print(f"📝 Error details: {error_str[:200]}...")
                        print(f"⏱️  Waiting {delay} seconds before retry...")
                        print(f"💡 Tip: Consider upgrading Azure OpenAI tier for higher limits")
                        
                        # Show progress during wait
                        await self._wait_with_progress(delay)
                        continue
                    else:
                        print(f"❌ Max retries ({self.max_retries}) exceeded for rate limiting")
                        print(f"💳 Consider upgrading your Azure OpenAI pricing tier:")
                        print(f"   https://aka.ms/oai/quotaincrease")
                        raise
                else:
                    # Non-rate-limit error, re-raise immediately
                    raise
        
        # Should never reach here
        raise Exception("Unexpected end of retry loop")
    
    async def _wait_with_progress(self, total_seconds: int):
        """Wait with progress indicator."""
        
        for remaining in range(total_seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            time_str = f"{mins:02d}:{secs:02d}" if mins > 0 else f"00:{secs:02d}"
            print(f"\r⏳ Waiting... {time_str} remaining", end="", flush=True)
            await asyncio.sleep(1)
        
        print("\r✅ Wait complete, retrying...                    ")


def setup_args():
    """Setup enhanced arguments with rate limit options."""
    parser = argparse.ArgumentParser(
        description="Robust distributed transcription processor with rate limit handling",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--file", "-f", required=True, help="Input transcription file")
    parser.add_argument("--documents", "-d", nargs="*", default=[], help="Additional documents")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retries for rate limits (default: 3)")
    parser.add_argument("--retry-delay", type=int, default=60, help="Base retry delay in seconds (default: 60)")
    parser.add_argument("--chunk-size", type=int, default=800, help="Smaller chunks for rate limit management")
    
    return parser.parse_args()


def prepare_multimodal_context(documents: List[str]) -> str:
    """Prepare multimodal context information."""
    
    context_info = []
    
    if documents:
        context_info.append(f"\n**DOCUMENTOS ADICIONALES DISPONIBLES:**")
        for doc in documents:
            doc_path = Path(doc)
            if doc_path.exists():
                context_info.append(f"- {doc_path.name}: Documento de referencia")
            else:
                context_info.append(f"- {doc_path.name}: [NO ENCONTRADO]")
    
    if context_info:
        context_info.append("\n**INSTRUCCIÓN**: Usar documentos para enriquecer respuestas.")
        return "\n".join(context_info)
    
    return ""


async def main():
    """Robust main processing with rate limit handling."""
    
    print("🛡️ ROBUST DISTRIBUTED SYSTEM WITH RATE LIMIT HANDLING")
    print("🔄 Auto-retry on 429 errors • ⏱️ Smart backoff • 📊 Progress tracking")
    print()
    
    args = setup_args()
    
    # Initialize rate limit handler
    rate_handler = RateLimitHandler(
        max_retries=args.max_retries,
        base_delay=args.retry_delay
    )
    
    try:
        # Load transcription content
        input_path = Path(args.file)
        if not input_path.exists():
            print(f"❌ File not found: {args.file}")
            return
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        original_words = len(content.split())
        print(f"📁 Loaded: {original_words:,} words from {args.file}")
        
        # Check multimodal files
        valid_multimodal = [f for f in args.documents if Path(f).exists()]
        
        if valid_multimodal:
            print(f"🖼️  Multimodal context: {len(valid_multimodal)} files")
            for file in valid_multimodal:
                print(f"   • {Path(file).name}")
        
        # STEP 1: Adaptive format detection and segmentation  
        print(f"🔍 Analyzing content format and segmenting adaptively...")
        segments, recommended_agent = adaptive_segment_content(content)
        print(f"✅ Created {len(segments)} segments using adaptive method")
        
        # Prepare enhanced content with multimodal context
        multimodal_context = prepare_multimodal_context(args.documents)
        
        print(f"\n🛡️ Rate limit protection: {args.max_retries} retries, {args.retry_delay}s base delay")
        print(f"⚡ Processing each segment individually with LLM agents...")
        
        start_time = time.time()
        
        # Process each segment with rate limit protection using adaptive agent
        async def process_operation():
            # Choose the appropriate FastAgent instance based on recommendation
            if recommended_agent == "meeting_processor":
                print(f"🎯 Using specialized meeting processor for diarized content")
                agent_instance = meeting_fast
                processor_name = "meeting_processor"
            else:
                print(f"🎯 Using standard processor for linear content")  
                agent_instance = fast
                processor_name = "simple_processor"
            
            async with agent_instance.run() as agent_app:
                # Process segments individually with appropriate agent
                processed_segments = []
                
                for i, segment in enumerate(segments, 1):
                    print(f"🔄 Processing segment {i}/{len(segments)} with {processor_name}...")
                    
                    # Add multimodal context to segment
                    segment_with_context = segment + multimodal_context if multimodal_context else segment
                    
                    # Process this segment through the appropriate LLM pipeline
                    if recommended_agent == "meeting_processor":
                        result = await agent_app.meeting_processor.send(segment_with_context)
                    else:
                        result = await agent_app.simple_processor.send(segment_with_context)
                    
                    processed_segments.append(result)
                
                # Combine all processed segments
                final_result = "\n\n".join(processed_segments)
                return final_result
        
        # Execute with automatic retry on rate limits
        result = await rate_handler.execute_with_retry(process_operation)
        
        processing_time = time.time() - start_time
        
        if not result:
            print("❌ No result generated")
            return
        
        # Save result
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            input_name = input_path.stem
            output_path = Path(f"robust_result_{input_name}_{timestamp}.md")
        
        # Enhanced metadata with retry info
        retry_info = f"<!-- Retries needed: {rate_handler.retry_count} -->" if rate_handler.retry_count > 0 else ""
        
        metadata = f"""<!-- Robust Enhanced Processing with Rate Limit Handling -->
<!-- Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} -->
<!-- Source: {args.file} -->
<!-- Processing time: {processing_time:.1f} seconds -->
{retry_info}
{'<!-- Multimodal Documents: ' + ', '.join([Path(d).name for d in args.documents]) + ' -->' if args.documents else ''}

"""
        
        final_content = metadata + result
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        # Enhanced statistics
        result_words = len(result.split())
        retention = (result_words / original_words * 100) if original_words > 0 else 0
        
        qa_count = result.count("#### Pregunta")
        segment_count = result.count("### Segmento")
        
        print("\n✅ ROBUST PROCESSING COMPLETE")
        print("=" * 50)
        print(f"📊 Input words: {original_words:,}")
        print(f"📊 Output words: {result_words:,}")
        print(f"📊 Content retention: {retention:.1f}%")
        print(f"📊 Segments processed: {segment_count}")
        print(f"📊 Q&A generated: {qa_count} questions")
        print(f"⏱️ Total time: {processing_time:.1f} seconds")
        print(f"🔄 Retries used: {rate_handler.retry_count}")
        print(f"📁 Saved to: {output_path}")
        
        if valid_multimodal:
            print(f"🖼️  Multimodal context: {len(valid_multimodal)} files integrated")
        
        print(f"\n🛡️ Rate Limit Handling:")
        if rate_handler.retry_count == 0:
            print(f"   • No rate limits encountered - smooth processing!")
        else:
            print(f"   • Successfully recovered from {rate_handler.retry_count} rate limit(s)")
            print(f"   • Consider upgrading Azure OpenAI tier for better performance")
        
        print("\n🎉 Robust processing completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "rate limit" in error_str.lower():
            print(f"\n❌ Rate limit error after all retries: {e}")
            print(f"💡 Solutions:")
            print(f"   1. Wait longer and try again")
            print(f"   2. Upgrade Azure OpenAI pricing tier: https://aka.ms/oai/quotaincrease")
            print(f"   3. Use smaller chunks: --chunk-size 500")
            print(f"   4. Increase retry delay: --retry-delay 90")
        else:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())