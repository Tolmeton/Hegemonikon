import sys
import os
import pickle
import traceback

sys.path.insert(0, os.path.abspath('20_機構｜Mekhane/_src｜ソースコード'))

from hermeneus.src.parser import CCLParser

def main():
    pkl_path = "30_記憶｜Mneme/02_索引｜Index/code.pkl"
    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)
        
    metadata = data.get('metadata', {})
    print(f"Loaded {len(metadata)} functions from code.pkl")
    
    parser = CCLParser()
    
    error_types = {}
    printed_errors = 0
    
    for k, v in list(metadata.items())[:1000]:
        ccl_expr = v.get('ccl_expr')
        if not ccl_expr:
            continue
        try:
            ast = parser.parse(ccl_expr)
        except Exception as e:
            err_msg = str(e)
            if "ParseError" in repr(e) or "UnexpectedCharacters" in repr(e) or "UnexpectedToken" in repr(e):
                err_type = type(e).__name__
            else:
                err_type = str(e).split('\n')[0][:100]
                
            error_types[err_type] = error_types.get(err_type, 0) + 1
            if printed_errors < 5:
                print(f"Error parsing: {ccl_expr}")
                print(f"Exception: {repr(e)}")
                printed_errors += 1
                
    print("\nError types summary:")
    for k, v in error_types.items():
        print(f"  {k}: {v}")

if __name__ == '__main__':
    main()
