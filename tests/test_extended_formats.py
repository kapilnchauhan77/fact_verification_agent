"""
Test script for extended document format support
"""
import tempfile
import json
from pathlib import Path
from src.fact_check_agent.document_processor import DocumentProcessor

def create_test_files():
    """Create test files in various formats"""
    test_files = {}
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    
    # Text file
    txt_file = temp_dir / "test.txt"
    with open(txt_file, 'w') as f:
        f.write("This is a test document with factual claims.\nAccording to NASA, Earth orbits the Sun.")
    test_files['txt'] = txt_file
    
    # Markdown file
    md_file = temp_dir / "test.md"
    with open(md_file, 'w') as f:
        f.write("# Test Document\n\nThis is a **markdown** document.\n\nAccording to WHO, handwashing prevents disease.")
    test_files['md'] = md_file
    
    # HTML file
    html_file = temp_dir / "test.html"
    with open(html_file, 'w') as f:
        f.write("""
        <html>
        <head><title>Test HTML</title></head>
        <body>
        <h1>Test Document</h1>
        <p>According to the CDC, vaccines are <strong>95% effective</strong>.</p>
        </body>
        </html>
        """)
    test_files['html'] = html_file
    
    # RTF file
    rtf_file = temp_dir / "test.rtf"
    with open(rtf_file, 'w') as f:
        f.write(r"""{\rtf1\ansi\deff0 {\fonttbl {\f0 Times New Roman;}}
        \f0\fs24 This is an RTF document. According to research, exercise reduces heart disease by 35%.}""")
    test_files['rtf'] = rtf_file
    
    # XML file
    xml_file = temp_dir / "test.xml"
    with open(xml_file, 'w') as f:
        f.write("""<?xml version="1.0"?>
        <document>
        <title>Test XML</title>
        <content>According to studies, meditation reduces stress by 40%.</content>
        </document>
        """)
    test_files['xml'] = xml_file
    
    return test_files

def test_extended_formats():
    """Test the extended document format support"""
    print("🔍 Testing Extended Document Format Support")
    print("=" * 50)
    
    processor = DocumentProcessor()
    
    # Show supported formats
    formats_info = processor.get_supported_formats_info()
    print("\n📋 Supported Format Categories:")
    for category, formats in formats_info.items():
        print(f"  {category.upper()}: {', '.join(formats)}")
    
    # Create test files
    print("\n📁 Creating test files...")
    test_files = create_test_files()
    
    # Test each format
    results = {}
    
    for format_name, file_path in test_files.items():
        try:
            print(f"\n🔄 Testing {format_name.upper()} format...")
            result = processor.process_document(file_path)
            
            if result['success']:
                print(f"  ✅ Success: {result['word_count']} words extracted")
                print(f"  📝 Method: {result['metadata']['processing_method']}")
                print(f"  📄 Preview: {result['text'][:100]}...")
                
                results[format_name] = {
                    'success': True,
                    'word_count': result['word_count'],
                    'method': result['metadata']['processing_method'],
                    'preview': result['text'][:100]
                }
            else:
                print(f"  ❌ Failed to extract text")
                results[format_name] = {'success': False}
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results[format_name] = {'success': False, 'error': str(e)}
    
    # Summary
    print(f"\n📊 Test Summary:")
    successful = sum(1 for r in results.values() if r.get('success', False))
    total = len(results)
    print(f"  Successfully processed: {successful}/{total} formats")
    
    for format_name, result in results.items():
        status = "✅" if result.get('success', False) else "❌"
        print(f"  {status} {format_name.upper()}")
    
    # Cleanup
    print(f"\n🧹 Cleaning up test files...")
    for file_path in test_files.values():
        try:
            file_path.unlink()
            file_path.parent.rmdir()
        except:
            pass
    
    return results

def test_format_detection():
    """Test automatic format detection and fallback mechanisms"""
    print("\n🔍 Testing Format Detection & Fallbacks")
    print("=" * 40)
    
    processor = DocumentProcessor()
    
    # Create a file with unknown extension but text content
    temp_dir = Path(tempfile.mkdtemp())
    unknown_file = temp_dir / "test.unknown"
    
    with open(unknown_file, 'w') as f:
        f.write("This is a text file with unknown extension.\nAccording to scientists, water boils at 100°C.")
    
    try:
        print("📄 Testing unknown format detection...")
        result = processor.process_document(unknown_file)
        
        if result['success']:
            print(f"  ✅ Successfully processed unknown format")
            print(f"  📝 Method: {result['metadata']['processing_method']}")
            print(f"  📄 Text: {result['text'][:100]}...")
        else:
            print(f"  ❌ Failed to process unknown format")
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    finally:
        # Cleanup
        unknown_file.unlink()
        temp_dir.rmdir()

def test_processing_capabilities():
    """Test advanced processing capabilities"""
    print("\n⚙️  Testing Advanced Processing Capabilities")
    print("=" * 45)
    
    processor = DocumentProcessor()
    
    # Test metadata extraction
    temp_dir = Path(tempfile.mkdtemp())
    test_file = temp_dir / "metadata_test.txt"
    
    with open(test_file, 'w') as f:
        f.write("Sample content for metadata testing.")
    
    print("📋 Testing metadata extraction...")
    metadata = processor.extract_document_metadata(test_file)
    
    print("  Metadata extracted:")
    for key, value in metadata.items():
        print(f"    {key}: {value}")
    
    # Test file size limits
    print(f"\n📏 Testing file size limits...")
    from src.fact_check_agent.config from src.fact_check_agent import config
    print(f"  Max file size: {config.max_document_size_mb} MB")
    print(f"  Supported formats: {len(config.supported_formats)} total")
    
    # Cleanup
    test_file.unlink()
    temp_dir.rmdir()

def main():
    """Run all tests"""
    print("🚀 Extended Document Processor Test Suite")
    print("=" * 60)
    
    try:
        # Test basic format support
        format_results = test_extended_formats()
        
        # Test format detection
        test_format_detection()
        
        # Test advanced capabilities
        test_processing_capabilities()
        
        print(f"\n🎉 All tests completed!")
        
        # Show final summary
        successful_formats = [f for f, r in format_results.items() if r.get('success', False)]
        print(f"\n✅ Successfully supported formats: {', '.join(successful_formats)}")
        
        print(f"\n💡 Tips for using the extended processor:")
        print(f"  • Use processor.get_supported_formats_info() to see all categories")
        print(f"  • Archive files are automatically extracted and processed")
        print(f"  • Audio/video files require additional dependencies")
        print(f"  • Unknown formats use intelligent fallback detection")
        
    except Exception as e:
        print(f"❌ Test suite failed: {str(e)}")

if __name__ == "__main__":
    main()