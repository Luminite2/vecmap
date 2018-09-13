#!/usr/bin/env python3
import embeddings

def debug():
  pass
  #get x and xw
  #w = x(-1)xw

def checkc2iauto():
  xfn = "data/embeddings/unit-center/en.emb.txt"
  zfn1 = "data/embeddings/unit-center/it.emb.txt"
  zfn2 = "output/acl2017/en-it/numerals/1gram1/it.emb.txt"
  with open(zfn1, encoding='utf-8', errors='surrogateescape') as zf1:
    with open(xfn, encoding='utf-8', errors='surrogateescape') as xf:
      (srcs, x), (trgs, z), c2i = embeddings.orthoread(zf1,xf,1,1,c2i=True)
      with open(zfn2, encoding='utf-8', errors='surrogateescape') as zf2:
        _, z2 = embeddings.read(zf2)
        #z==z2?
        print(z==z2)

  #orthoread z, check == mapz

def checkc2iconsistencymanual():
  sf = "data/embeddings/unit-center/en.emb.txt"
  tf = "data/embeddings/unit-center/it.emb.txt"
  with open(sf, encoding='utf-8', errors='surrogateescape') as sff:
    with open(tf, encoding='utf-8', errors='surrogateescape') as tff:
      (srcs, x), (trgs, z), c2i = embeddings.orthoread(sff,tff,1,1, c2i=True)
      for e in c2i:
        try:
          print("{}: {}".format(e,c2i[e]))
        except UnicodeEncodeError:
          print("[Error]: {}".format(c2i[e]))

def main():
  checkc2iauto()

if __name__ == "__main__":
  main()

