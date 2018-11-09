import numpy as np

def ngrammer(n):
  return lambda w: [w[index:index+n] for index in range(len(w)-n+1)]

def ngram_alphabet(words, char_n):
  ngrams = ngrammer(char_n)
  alphabet = set()
  for word in words:
    for ngram in ngrams(word):
      alphabet.add(ngram)
  return alphabet


def extend_word_embeddings(words, matrix, ngram_index, scale, char_n, dtype):
  ngrams = ngrammer(char_n)
  extensions = np.zeros((len(words),len(ngram_index)),dtype=dtype)
  for i,word in enumerate(words):
    extension = np.zeros(len(ngram_index))
    for ngram in ngrams(word):
      extension[ngram_index[ngram]] += scale
    #extensions.append(extension)
    extensions[i] = extension
  matrix = np.append(matrix, extensions, 1)
  matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
  return matrix

def extend_bilingual_embeddings(s_words, s_matrix, t_words, t_matrix, scale, char_n=1, dtype='float'):
  alphabet = sorted(list(ngram_alphabet(s_words, char_n).union(ngram_alphabet(t_words, char_n))))
  #sort them, then c2i
  ngram_index = {k:v for v,k in enumerate(alphabet)}
  s_matrix = extend_word_embeddings(s_words, s_matrix, ngram_index, scale, char_n, dtype)
  t_matrix = extend_word_embeddings(t_words, t_matrix, ngram_index, scale, char_n, dtype)

  return s_matrix, t_matrix
  #
