#!/bin/bash
#
# Copyright (C) 2018  Parker Riley <prkriley@gmail.com>
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

ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DATA="$ROOT/data"
OUTPUT="$ROOT/output/acl2018ortho"

METHOD_COUNT=4
METHOD_IDS=('artetxe2017' 'extension_8' 'similarity_1' 'combined_8_1')
METHOD_NAMES=('Artetxe et al. (2017)' 'Embedding Extension, c_e = 1/8' 'Similarity adjustment, c_s = 1' 'Combined, c_e = 1/8, c_s = 1')
METHOD_TRAIN_ARGS=('--self_learning' '--self_learning --orthographic_ext=8' '--self_learning --orthographic_sim=1' '--self_learning --orthographic_ext=8 --orthographic_sim=1')
METHOD_EVAL_ARGS=('--dot' '--dot' '--dot' '--dot' '--dot')
METHOD_EMBEDDINGS=('unit-center' 'unit-center' 'unit-center' 'unit-center' 'unit-center')

EVAL_COUNT=2
EVAL_NAMES=('' ' (+Identity)')
EVAL_ARGS=('' '--identity')

LANGUAGE_COUNT=3
LANGUAGE_SRCS=('en' 'en' 'en')
LANGUAGE_TRGS=('it' 'de' 'fi')
LANGUAGE_NAMES=('ENGLISH-ITALIAN' 'ENGLISH-GERMAN' 'ENGLISH-FINNISH')

DICTIONARY_COUNT=1
DICTIONARY_IDS=('numerals')
DICTIONARY_NAMES=('NUMERAL DICTIONARY')
DICTIONARY_SIZES=('0')
DICTIONARY_TRAIN_ARGS=('--numerals')

I_START=${1:-0}
J_START=${2:-0}
K_START=${3:-0}

for ((i = I_START; i < $LANGUAGE_COUNT; i++))
do
    src=${LANGUAGE_SRCS[$i]}
    trg=${LANGUAGE_TRGS[$i]}
    echo '--------------------------------------------------------------------------------'
    echo ${LANGUAGE_NAMES[$i]}
    echo '--------------------------------------------------------------------------------'
    for ((j = J_START; j < $DICTIONARY_COUNT; j++))
    do
        echo ${DICTIONARY_NAMES[$j]}
        for ((k = K_START; k < $METHOD_COUNT; k++))
        do
            embedding_dir="$DATA/embeddings/${METHOD_EMBEDDINGS[$k]}"
            output_dir="$OUTPUT/$src-$trg/${DICTIONARY_IDS[$j]}/${METHOD_IDS[$k]}"
            mkdir -p "$output_dir"
            args="${METHOD_TRAIN_ARGS[$k]} ${DICTIONARY_TRAIN_ARGS[$j]}"
            head -${DICTIONARY_SIZES[$j]} "$DATA/dictionaries/$src-$trg.train.shuf.txt" | python3 "$ROOT/map_embeddings.py" "$embedding_dir/$src.emb.txt" "$embedding_dir/$trg.emb.txt" "$output_dir/$src.emb.txt" "$output_dir/$trg.emb.txt" $args
            for ((l = 0; l < $EVAL_COUNT; l++))
            do
              method_name="${METHOD_NAMES[$k]}${EVAL_NAMES[$l]}"
              echo -n "  - $method_name  |  Translation"
              eval_args="${METHOD_EVAL_ARGS[$k]} ${EVAL_ARGS[$l]}"
              python3 "$ROOT/eval_translation.py" $eval_args -d "$DATA/dictionaries/$src-$trg.test.txt" "$output_dir/$src.emb.txt" "$output_dir/$trg.emb.txt" | grep -Eo ':[^:]+%' | tail -1 | tr -d '\n'
              echo
            done
        done
    done
    echo
done
