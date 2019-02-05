# Copyright (C) 2016-2018  Mikel Artetxe <artetxem@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from cupy_utils import *

import numpy as np
import orthographic


def read(file, threshold=0, vocabulary=None, dtype='float'):
    header = file.readline().split(' ')
    count = int(header[0]) if threshold <= 0 else min(threshold, int(header[0]))
    dim = int(header[1])
    words = []
    matrix = np.empty((count, dim), dtype=dtype) if vocabulary is None else []
    for i in range(count):
        word, vec = file.readline().split(' ', 1)
        if vocabulary is None:
            words.append(word)
            matrix[i] = np.fromstring(vec, sep=' ', dtype=dtype)
        elif word in vocabulary:
            words.append(word)
            matrix.append(np.fromstring(vec, sep=' ', dtype=dtype))
    return (words, matrix) if vocabulary is None else (words, np.array(matrix, dtype=dtype))

def ortho_read(s_file, t_file, scale, char_n=1, threshold=0, s_vocab=None, t_vocab=None, dtype='float', unigram_limit=None):
  s_words, s_matrix = read(s_file, threshold, s_vocab, dtype)
  t_words, t_matrix = read(t_file, threshold, t_vocab, dtype)

  s_matrix, t_matrix = orthographic.extend_bilingual_embeddings(s_words, s_matrix, t_words, t_matrix, scale, char_n, dtype, unigram_limit=unigram_limit)
  return (s_words, s_matrix), (t_words, t_matrix)

def write(words, matrix, file):
    m = asnumpy(matrix)
    print('%d %d' % m.shape, file=file)
    for i in range(len(words)):
        print(words[i] + ' ' + ' '.join(['%.6g' % x for x in m[i]]), file=file)


def length_normalize(matrix):
    xp = get_array_module(matrix)
    norms = xp.sqrt(xp.sum(matrix**2, axis=1))
    norms[norms == 0] = 1
    matrix /= norms[:, xp.newaxis]


def mean_center(matrix):
    xp = get_array_module(matrix)
    avg = xp.mean(matrix, axis=0)
    matrix -= avg


def length_normalize_dimensionwise(matrix):
    xp = get_array_module(matrix)
    norms = xp.sqrt(xp.sum(matrix**2, axis=0))
    norms[norms == 0] = 1
    matrix /= norms


def mean_center_embeddingwise(matrix):
    xp = get_array_module(matrix)
    avg = xp.mean(matrix, axis=1)
    matrix -= avg[:, xp.newaxis]


def normalize(matrix, actions):
    for action in actions:
        if action == 'unit':
            length_normalize(matrix)
        elif action == 'center':
            mean_center(matrix)
        elif action == 'unitdim':
            length_normalize_dimensionwise(matrix)
        elif action == 'centeremb':
            mean_center_embeddingwise(matrix)


def get_embeddings(l1, l2, **kwargs):
  import time
  import sys
  verbose = False
  if "verbose" in kwargs:
    verbose = kwargs["verbose"]
  if verbose:
    print("Beginning!")
    sys.stdout.flush()
  start = time.time()
  base = "./data/embeddings"
  if "base" in kwargs:
    base = kwargs["base"]
  srcF = open("{}/{}.emb.txt".format(base,l1), encoding="utf-8", errors="surrogateescape")
  trgF = open("{}/{}.emb.txt".format(base,l2), encoding="utf-8", errors="surrogateescape")
  srcs, x = read(srcF)
  t1 = time.time()
  if verbose:
    print("Read source embeddings, time: {}".format(t1-start))
  trgs, z = read(trgF)
  t2 = time.time()
  if verbose:
    print("Read target embeddings, time: {}".format(t2-t1))
  return srcs, x, trgs, z

def vocab_with_indices(l1, l2, **kwargs):
  srcs, x, trgs, z = get_embeddings(l1,l2,**kwargs)
  src_word2ind = {word: i for i, word in enumerate(srcs)}
  trg_word2ind = {word: i for i, word in enumerate(trgs)}
  return srcs, x, trgs, z, src_word2ind, trg_word2ind

def create_and_save_similarity_matrix(l1,l2,k,fpath,ep,src_cutoff=None,trg_cutoff=None):
  srcs, _, trgs, _, src_word2ind, trg_word2ind = vocab_with_indices(l1,l2)

  simmat = orthographic.similarity_matrix(srcs,trgs,src_word2ind,trg_word2ind,k,ep,src_cutoff=src_cutoff,trg_cutoff=trg_cutoff)
  save_sparse_csr(fpath, simmat)
  return simmat

def load_or_create_similarity_matrix(l1,l2,k,ep=None,src_cutoff=None,trg_cutoff=None): #TODO: add arg for alg selection
  fpath = orthographic.similarity_matrix_filename(l1,l2,k,ep)
  simmat = None
  try:
    simmat = load_sparse_csr(fpath)
  except IOError:
    simmat = create_and_save_similarity_matrix(l1,l2,k,fpath,ep,src_cutoff=src_cutoff,trg_cutoff=trg_cutoff)
  return simmat

def save_sparse_csr(fname, array):
  import numpy as np
  np.savez(fname, data = array.data, indices = array.indices, indptr = array.indptr, shape = array.shape)

def load_sparse_csr(fname):
  import numpy as np
  from scipy.sparse import csr_matrix
  loader = np.load(fname)
  return csr_matrix((loader['data'], loader['indices'], loader['indptr']), shape = loader['shape'])


