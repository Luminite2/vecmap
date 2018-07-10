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

def similarity(w1,w2):
  import math
  ed = editDist(w1,w2)
  return math.log(2.0-ed)

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

def getEmbeds(l2, l1="en", **kwargs):
  import time
  import sys
  verbose = False
  if "verbose" in kwargs:
    verbose = kwargs["verbose"]
  if verbose:
    print("Beginning!")
    sys.stdout.flush()
  start = time.time()
  base = "./data/embeddings/unit-center"
  if "base" in kwargs:
    base = kwargs["base"]
  srcF = open("{}/{}.emb.txt".format(base,l1), encoding="utf-8", errors="surrogateescape")
  trgF = open("{}/{}.emb.txt".format(base,l2), encoding="utf-8", errors="surrogateescape")
  srcs, x = embeddings.read(srcF)
  t1 = time.time()
  if verbose:
    print("Read source embeddings, time: {}".format(t1-start))
  trgs, z = embeddings.read(trgF)
  t2 = time.time()
  if verbose:
    print("Read target embeddings, time: {}".format(t2-t1))
  return srcs, x, trgs, z


def makeDicts(l2, l1="en"):
  srcs, _, trgs, _ = getEmbeds(l2,l1)
  src_start = 0
  k = 1
  with open("./data/dictionaries/{}-{}.ortho_{}.k_{}.txt".format(l1, l2, src_start, k), "w", 1, encoding="utf-8", errors="surrogateescape") as f:
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

def save_sparse_csr(fname, array):
  import numpy as np
  np.savez(fname, data = array.data, indices = array.indices, indptr = array.indptr, shape = array.shape)

def load_sparse_csr(fname='en-it_simMatrix_1.npz'):
  import numpy as np
  from scipy.sparse import csr_matrix
  loader = np.load(fname)
  return csr_matrix((loader['data'], loader['indices'], loader['indptr']), shape = loader['shape'])

def vocabWIndices(l2, l1="en", **kwargs):
  srcs, x, trgs, z = getEmbeds(l2,l1,**kwargs)
  src_word2ind = {word: i for i, word in enumerate(srcs)}
  trg_word2ind = {word: i for i, word in enumerate(trgs)}
  return srcs, x, trgs, z, src_word2ind, trg_word2ind

def similarityMatrix(l2,l1="en"):
  import numpy as np
  import tables
  from scipy.sparse import lil_matrix
  from scipy.sparse import csr_matrix

  k = 1
  fpath = "{}-{}_simMatrix_{}.npz".format(l1,l2,k)
  srcs, _, trgs, _, src_word2ind, trg_word2ind = vocabWIndices(l2,l1)
  simmat = lil_matrix((len(srcs),len(trgs)), dtype='float64')
  trgmap = lexDeleteAugment(trgs,k)
  for w in srcs:
    if len(w) > 30:
      continue
    for cand in matches(trgmap,w,k):
      sim = similarity(w,cand)
      simmat[src_word2ind[w],trg_word2ind[cand]] = sim
  save_sparse_csr(fpath, simmat.tocsr())
  #return simmat
  #TODO: using symmetric bizzle wizzle, record ALL scores
  #put it in numpy array, make sure dimensions line up with embeddings

  #get trgmap
  #for candidates in augmented srcs
    #if in there, get similarity score (1 + log whatever), put in matrix at right position
  #return matrix

def objective(xw,z):
  import numpy as np

  MAX_DIM_Z = 10000
  MAX_DIM_X = 10000
  #xw = xw[:100]
  #z = z[:100]
  best_sim = np.full(xw.shape[0], -100.)
  for i in range(0, xw.shape[0], MAX_DIM_X):
    for j in range(0, z.shape[0], MAX_DIM_Z):
      sim = xw[i:i+MAX_DIM_X].dot(z[j:j+MAX_DIM_Z].T)
      for k in range(sim.shape[0]):
        l = sim[k].argmax()
        if sim[k, l] > best_sim[i+k]:
          best_sim[i+k] = sim[k, l]

  return np.mean(best_sim)

def get_objective(l2, method,l1="en"):
  base = "./output/acl2017/{}-{}/numerals/{}".format(l1,l2,method)
  srcs, xw, trgs, z, src2ind, trg2ind = vocabWIndices(l2,l1,base=base)
  normal_objective = objective(xw,z)
  xw = xw[:,:300]
  z = z[:,:300]
  new_objective = objective(xw,z)
  print("-----\n{}-{} {}\nOld:{}\nNew:{}\n-----".format(l1,l2,method,normal_objective,new_objective))

def main():
  #similarityMatrix("fi")
  #simmat.dump("en-it_simMatrix.pkl")
  #get_objective("it","1gram4")
  #get_objective("it","1gram5")
  #get_objective("it","1gram6")
  #get_objective("it","1gram7")
  #get_objective("it","1gram8")
  get_objective("it","1gram10")
  get_objective("it","1gram16")
  get_objective("it","1gram1000000")

if __name__ == "__main__":
  main()
  #clean("data/dictionaries/en-it.ortho.k_2.txt")
#take target dictionary and process it
#for each source word, get allDeletes...K, concat all entries in hash, if we found some then eval them to find best edit distance, use it as dict entry
