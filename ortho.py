import itertools
import embeddings

def editDist(w1,w2):
    l1 = len(w1)
    l2 = len(w2)
    if (l1 == 0) or (l2 == 0):
        return 1.0
    D = [[1e100 for j in range(l2+1)] for i in range(l1+1)]
    for i in range(1,l1+1):
        D[i][0] = float(i)
    for j in range(1,l2+1):
        D[0][j] = float(j)
    D[0][0] = 0.0
    for j in range(1,l2+1):
        for i in range(1,l1+1):
            a = D[i-1][j] + 1
            b = D[i][j-1] + 1
            diff = 0.0 if w1[i-1] == w2[j-1] else 1.0
            c = D[i-1][j-1] + diff

            if a <= b and a <= c:
                D[i][j] = a
            elif b <= a and b <= c:
                D[i][j] = b
            elif c <= a and c <= b:
                D[i][j] = c
    denom = 1.0
    if l1 >= l2:
        denom = l1
    else:
        denom = l2

    return float(D[l1][l2]) / float(denom)

def allDeletesUpToK(word, k):
  l = []
  for i in range(k+1):
    for poss in itertools.combinations(range(len(word)),i):
      w = word
      j = 0
      for p in poss:
        w = w[:p-j] + w[p-j+1:]
        j += 1
      l.append(w)
  return l

def lexDeleteAugment(lex, k):
  d = {}
  for w in lex:
    #generate all types
    edits = allDeletesUpToK(w,k)
    #hash them all to w (add to list)
    for edit in edits:
      if edit not in d:
        d[edit] = [w]
      else:
        d[edit].append(w)
  return d

def makeDictFile(outF, srcs, trgs, k, src_start=0):
  import time
  import sys
  print("Augmenting target!")
  t1 = time.time()
  trgmap = lexDeleteAugment(trgs, k)
  t2 = time.time()
  print("Augmented target in time: {}".format(t2-t1))
  i = src_start
  for w in srcs[src_start:]:
    if i%5000 == 0:
      print("Processing source word {}".format(i))
      sys.stdout.flush()
    elif i > 100000 and i%1000 == 0:
      print("Processing source word {}".format(i))
      sys.stdout.flush()
    i += 1
    if len(w) > 30:
      continue
    candidates = []
    dels = allDeletesUpToK(w,k)
    for d in dels:
      if d in trgmap:
        candidates += trgmap[d]
    bestdist = None
    bestword = None
    for c in candidates:
      dist = editDist(w,c)
      if bestdist == None or dist < bestdist:
        bestdist = dist
        bestword = c
    if bestword != None:
      outF.write("{} {}\n".format(w,bestword))

def matches(tmap, w, k):
  cands = []
  for d in allDeletesUpToK(w,k):
    if d in tmap:
      cands += tmap[d]
  return cands

def debug(srcs, trgs, k):
  trgmap = lexDeleteAugment(trgs,k)
  maxlen = 0
  for w in srcs[114000:115000]:
    cands = []
    dels = allDeletesUpToK(w,k)
    for d in dels:
      if d in trgmap:
        cands += trgmap[d]
    if len(cands) > maxlen:
      maxlen = len(cands)
      print("{}".format(len(maxlen)))

def getEmbeds():
  import time
  import sys
  print("Beginning!")
  sys.stdout.flush()
  start = time.time()
  srcF = open("./data/embeddings/unit/en.emb.txt", encoding="utf-8", errors="surrogateescape")
  trgF = open("./data/embeddings/unit/it.emb.txt", encoding="utf-8", errors="surrogateescape")
  srcs, x = embeddings.read(srcF)
  t1 = time.time()
  print("Read source embeddings, time: {}".format(t1-start))
  trgs, z = embeddings.read(trgF)
  t2 = time.time()
  print("Read target embeddings, time: {}".format(t2-t1))
  return srcs, x, trgs, z


def makeDicts():
  srcs, _, trgs, _ = getEmbeds()
  src_start = 0
  k = 1
  with open("./data/dictionaries/en-it.ortho_{}.k_{}.txt".format(src_start, k), "w", 1, encoding="utf-8", errors="surrogateescape") as f:
    makeDictFile(f, srcs, trgs, k, src_start)

def clean(fname):
  with open(fname, 'r',encoding='utf-8',errors='surrogateescape') as f:
    i = 0
    with open(fname+"_clean",'w',encoding='utf-8',errors='surrogateescape') as fout:
      for line in f:
        ps = line.split()
        if len(ps) == 2:
          #print("i: {}, line: {}".format(i,line))
          fout.write(line)
        i += 1

def makeSimilarityMatrix():
  srcs, _, trgs, _ = getEmbeds()
  k = 1
  trgmap = lexDeleteAugment(trgs,k)
  for w in srcs:
    if len(w) > 30:
      continue
    for cand in matches(trgmap,w,k):
      ed = editDist(w,cand)
      pass


  pass
  #TODO: using symmetric bizzle wizzle, record ALL scores
  #put it in numpy array, make sure dimensions line up with embeddings

  #get trgmap
  #for candidates in augmented srcs
    #if in there, get similarity score (1 + log whatever), put in matrix at right position
  #return matrix

def main():
  pass

if __name__ == "__main__":
  main()
  #clean("data/dictionaries/en-it.ortho.k_2.txt")
#take target dictionary and process it
#for each source word, get allDeletes...K, concat all entries in hash, if we found some then eval them to find best edit distance, use it as dict entry
