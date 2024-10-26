from analyze_cid import analyze_cid, print_analysis

def test_ipfs():
    # Test both CID formats
    cids = [
        "bafybeicdn4wyj7e4rywuudatxhq3xmgpgtzfqvo6k5c2dybriepnfax2mi",  # IPFS v1
        "QmSstMLitD1FwFSkvd1r6cEELCpKmjVqH7b4ynRXqWQGBT"  # IPFS v0
    ]
    
    for cid in cids:
        print(f"\nTesting CID: {cid}")
        print("-" * 50)
        
        try:
            result = analyze_cid(cid)
            print_analysis(result)
        except Exception as e:
            print(f"Error processing CID {cid}: {str(e)}")

if __name__ == "__main__":
    test_ipfs()
