import embeddings

def debug():
  sf = "data/embeddings/unit-center/en.emb.txt"
  tf = "data/embeddings/unit-center/it.emb.txt"
  with open(sf, encoding='utf-8', errors='surrogateescape') as sff:
    with open(tf, encoding='utf-8', errors='surrogateescape') as tff:
      (srcs, x), (trgs, z), c2i = embeddings.orthoread(sff,tff,1,1, c2i=True)
      for e in c2i:
        print("{}: {}".format(e,c2i[e]))

def main():
  debug()

if __name__ == "__main__":
  main()

