import numpy as np
import itertools

import sys
sys.path.insert(0,'./edit-distance-learning')
import learnedit

def edit_dist(w1,w2):
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
  ed = edit_dist(w1,w2)
  return math.log(2.0-ed)

def ngrammer(n):
  return lambda w: [w[index:index+n] for index in range(len(w)-n+1)]

def ngram_alphabet(words, char_n):
  ngrams = ngrammer(char_n)
  alphabet = set()
  for word in words:
    for ngram in ngrams(word):
      alphabet.add(ngram)
  return alphabet


def extend_word_embeddings_deprecated(words, matrix, ngram_index, scale, char_n, dtype):
  ngrams = ngrammer(char_n)
  extensions = np.zeros((len(words),len(ngram_index)),dtype=dtype)
  for i,word in enumerate(words):
    extension = np.zeros(len(ngram_index))
    for ngram in ngrams(word):
      extension[ngram_index[ngram]] += scale #TODO: handle cases where alphabet is incomplete
    #extensions.append(extension)
    extensions[i] = extension
  matrix = np.append(matrix, extensions, 1)
  matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
  return matrix

def extend_word_embeddings(words, matrix, ngram_index, alphabet, scale, dtype):
  extensions = np.zeros((len(words),len(ngram_index)),dtype=dtype)
  for i,word in enumerate(words):
    extension = np.zeros(len(ngram_index))
    for j in range(len(word)):
      for ngram in alphabet.forward().prefixesOf(word[j:]):
        if ngram in ngram_index:
          extension[ngram_index[ngram]] += scale
    extensions[i] = extension
  matrix = np.append(matrix, extensions, 1)
  matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
  return matrix

def extend_bilingual_embeddings(s_words, s_matrix, t_words, t_matrix, scale, char_n=1, dtype='float',unigram_limit=None):
  #NOTE: char_n is deprecated
  #alphabet = sorted(list(ngram_alphabet(s_words, char_n).union(ngram_alphabet(t_words, char_n)))) #TODO: replace with Alphabet?
  s_alph = learnedit.Alphabet(s_words, unigram_limit=unigram_limit)
  t_alph = learnedit.Alphabet(t_words, unigram_limit=unigram_limit)
  alphabet = learnedit.Alphabet(*s_alph, *t_alph)
  #sort them, then c2i
  ngram_index = {k:v for v,k in enumerate(sorted(alphabet))}
  #s_matrix = extend_word_embeddings(s_words, s_matrix, ngram_index, scale, char_n, dtype)
  #t_matrix = extend_word_embeddings(t_words, t_matrix, ngram_index, scale, char_n, dtype)
  s_matrix = extend_word_embeddings(s_words, s_matrix, ngram_index, alphabet, scale, dtype)
  t_matrix = extend_word_embeddings(t_words, t_matrix, ngram_index, alphabet, scale, dtype)

  return s_matrix, t_matrix

def all_deletes_up_to_k(word, k):
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

def lex_delete_augment(lex, k):
  d = {}
  for w in lex:
    #generate all types
    edits = all_deletes_up_to_k(w,k)
    #if w == 'базы':
     # print('found базы!')
      #print('edits: {}'.format(edits))
    #hash them all to w (add to list)
    for edit in edits:
      if edit not in d:
        #d[edit] = [w]
        d[edit] = set([w])
      else:
        #d[edit].append(w)
        d[edit].add(w)
  return d

def similarity_matrix_filename(l1,l2,k,ep):
  ep_id = ''
  if ep:
    ep_id = '_ep' #TODO: better way?
  return "similarity_matrices/{}-{}_simMatrix_{}{}.npz".format(l1,l2,k,ep_id)

def matches(tmap, w, k):
  #cands = []
  cands = set()
  for d in all_deletes_up_to_k(w,k):
    if d in tmap:
      #cands += tmap[d]
      cands = cands.union(tmap[d])
  return cands

def similarity_matrix(srcs, trgs, src_word2ind, trg_word2ind,k,ep, src_cutoff=None, trg_cutoff=None):
  from scipy.sparse import lil_matrix
  from scipy.sparse import csr_matrix
  import math
  if src_cutoff:
    srcs = srcs[:src_cutoff]
  if trg_cutoff:
    trgs = trgs[:trg_cutoff]

  simmat = lil_matrix((len(srcs),len(trgs)), dtype='float64')
  trgmap = lex_delete_augment(trgs,k)
  if ep:
    translit = ep.transliterator_x2y()
    #trans_srcs = [translit(src) for src in srcs]
    #trans_src_word2ind = {translit(src):src_word2ind[src] for src in src_word2ind}
  num_sim_evald = 0
  nnz = 0
  translit_f = open('translit.out','w', encoding='utf-8')
  cand_f = open('pairs.out', 'w', encoding='utf-8')
  for w in srcs:
    #if w == 'bases':
    #  print('found bases!')
    if len(w) > 30:
      continue
    if ep:
      t = translit(w)
      translit_f.write('{} {}\n'.format(w,t))
      candidates = matches(trgmap,t,k)
      #if w == 'bases':
      #  print('translit: {}'.format(translit(w)))
      #  print('cands: {}'.format(candidates))
    else:
      candidates = matches(trgmap,w,k)
    for cand in candidates:
      if ep:
        cand_f.write('{} {}\n'.format(w,cand))
        sim = ep.score(w,cand)
        if sim != 0:
          sim = math.log(sim)/max(len(w),len(cand))
          sim *= 1.0 / math.log(len(ep.alph_x)*len(ep.alph_y))
          sim += 1.0
          sim = max(0,sim)
      else:
        sim = similarity(w,cand)
      num_sim_evald += 1
      if sim > 0.0:
        nnz += 1
      #if w not in src_word2ind:
      #  print('ERROR: {} not in src_word2ind!'.format(w))
      #if cand not in trg_word2ind:
      #  print('ERROR: {} not in trg_word2ind!'.format(cand))
      simmat[src_word2ind[w],trg_word2ind[cand]] = sim
  simmat = simmat.tocsr()
  print('evaluated similarity of {} pairs'.format(num_sim_evald))
  print('nnz: {}'.format(nnz))
  cand_f.close()
  translit_f.close()
  return simmat

