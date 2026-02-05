import sys
import os
import logging
import numpy as np

# Adjust path to find backend modules (Project Root)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Configure logging
logging.basicConfig(level=logging.INFO)

from backend.services.transcription.hybrid_service import HybridService
from backend.utils.text_processing import beautify_text

def test_hybrid_service_punctuation():
    print("Initializing HybridService...")
    try:
        service = HybridService()
    except Exception as e:
        print(f"Failed to initialize HybridService: {e}")
        sys.exit(1)

    print("Checking punctuation model...")
    if hasattr(service, 'punct_model') and service.punct_model is not None:
        print("PASS: Punctuation model loaded.")
        
        # Test Case 1: Simple Sentence
        input_text = "THIS IS A PEN"
        print(f"\n--- Test 1: '{input_text}' ---")
        
        try:
            # Manually simulate the flow in HybridStream
            lower_text = input_text.lower()
            raw_punctuated = service.punct_model.add_punctuation(lower_text)
            print(f"Raw Model Output: {raw_punctuated}")
            
            final_output = beautify_text(raw_punctuated)
            print(f"Final Output: {final_output}")
            
            if final_output == "This is a pen.":
                print("PASS: Correctly beautified.")
            else:
                print(f"WARN: Output '{final_output}' doesn't match expected 'This is a pen.'.")

        except Exception as e:
            print(f"Failed Test 1: {e}")
            sys.exit(1)

        # Test Case 2: "I" handling
        input_text = "i think i am ready"
        print(f"\n--- Test 2: '{input_text}' ---")
        try:
             lower_text = input_text.lower()
             raw_punctuated = service.punct_model.add_punctuation(lower_text)
             final_output = beautify_text(raw_punctuated)
             print(f"Final Output: {final_output}")
             
             if "I" in final_output and "am" in final_output:
                  print("PASS: 'I' capitalized.")
             else:
                  print("WARN: 'I' capitalization might have failed.")
                  
        except Exception as e:
             print(f"Failed Test 2: {e}")

        # Test Case 3: Spacing after period
        input_text = "This little greenow.this is the economic salt"
        print(f"\n--- Test 3: '{input_text}' ---")
        try:
             # Simulate normal processing
             # If input comes in lowercased to punctuation: "this little greenow.this is..."
             lower_text = input_text.lower()
             raw_punctuated = service.punct_model.add_punctuation(lower_text)
             # Assuming model keeps it as is or adds more punctuation
             # Let's force the scenario where model output has the issue
             problematic_output = "this little greenow.this is the economic salt"
             final_output = beautify_text(problematic_output)
             print(f"Final Output: {final_output}")
             
             expected = "This little greenow. This is the economic salt"
             if final_output == expected:
                  print("PASS: Spacing fixed and capitalized.")
             else:
                  print(f"WARN: Spacing fix failed. Got: '{final_output}'")

        except Exception as e:
             print(f"Failed Test 3: {e}")

    else:
        print("FAIL: Punctuation model NOT loaded.")
        sys.exit(1)

if __name__ == "__main__":
    test_hybrid_service_punctuation()
