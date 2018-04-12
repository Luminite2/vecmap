#!/usr/bin/env python3
import argparse

def idents(fname):
  tot = 0
  ident = 0
  with open(fname, encoding='utf-8', errors='surrogateescape') as d:
    for e,f in map(str.split, d.readlines()):
      tot +=1
      if e == f:
        ident += 1
    print("{}/{} = {}%".format(ident,tot,(float(ident)/tot)*100))

def getCorIncor(fname):
  import collections
  with open(fname, mode='r', errors='surrogateescape') as f:
    c = {}
    i = {}
    for l in f.readlines():
      parts = l.split()
      if parts[0].startswith('Correct:'):
        c[parts[0][8:]] = parts[1]
      elif parts[0].startswith('Incorrect:'):
        i[parts[0][10:]] = parts[1]
    return c,i

def interactiveInvestigate(trg, m2, m1="1gram7"):
  #trg, method1, method2
  compfn = "en-{}{}vs{}.compare".format(trg,m1,m2)
  c1i2, i1c2 = investigate(compfn)
  r1fn = "output/acl2017/en-{}/numerals/{}/en-{}.translation.test.split.results".format(trg,m1,trg)
  c1, i1 = getCorIncor(r1fn)
  r2fn = "output/acl2017/en-{}/numerals/{}/en-{}.translation.test.split.results".format(trg,m2,trg)
  c2, i2 = getCorIncor(r2fn)
  #given word, find what each method predicted
  def guess(w,b1):
    if b1:
      if w in c1:
        return c1[w]
      else:
        return i1[w]
    else:
      if w in c2:
        return c2[w]
      else:
        return i2[w]
  info = lambda w: "{}: {}({}): {}, {}({}): {}".format(w,m1,w in c1,guess(w,True),m2,w in c2,guess(w,False))
  return c1i2, i1c2, info

def investigate(fn):
  with open(fn,encoding='utf-8',mode='r') as f:
    ls = f.readlines()
    func = lambda s: s.replace(' ','')[1:-1]
    c1i2 = list(map(func,func(ls[13].strip()).split(',')))
    i1c2 = list(map(func,func(ls[17].strip()).split(',')))
    return c1i2, i1c2

def overlap(args):#fname1,fname2):
  fname1 = args.f1
  if args.investigate:
    return investigate(fname1)
  fname2 = args.f2
  c1,i1 = getCorIncor(fname1)
  c2,i2 = getCorIncor(fname2)
  both_c = []
  both_i = []
  only_c1 = []
  only_c2 = []
  uniq_c1 = []
  uniq_i1 = []
  uniq_c2 = []
  uniq_i2 = []

  for w in c1:
    p = w
    if w in c2:
      both_c.append(p)
    elif w in i2:
      only_c1.append(p)
    else:
      uniq_c1.append(p)

  for w in i1:
    p = w
    if w in i2:
      both_i.append(p)
    elif w not in c2:
      uniq_i1.append(p)

  for w in i2:
    p = w
    if w in i1:
      continue
    elif w not in c1:
      uniq_i2.append(p)

  for w in c2:
    p = w
    if w in c1:
      continue
    elif w in i1:
      only_c2.append(p)
    else:
      uniq_c2.append(p)

  print ("Comparing these two files:\n{}\n{}".format(fname1,fname2))
  print("Correct in both:\n{}\n{}\n\nIncorrect in both:\n{}\n{}\n\nCorrect in {}, incorrect in {}:\n{}\n{}\n\nCorrect in {}, incorrect in {}:\n{}\n{}\n\nCorrect in {}, not present in {}:\n{}\n{}\n\nIncorrect in {}, not present in {}:\n{}\n{}\n\nCorrect in {}, not present in {}:\n{}\n{}\n\nIncorrect in {}, not present in {}:\n{}\n{}\n".format(len(both_c),both_c,len(both_i),both_i,fname1,fname2,len(only_c1),only_c1,fname2,fname1,len(only_c2),only_c2,fname1,fname2,len(uniq_c1),uniq_c1,fname1,fname2,len(uniq_i1),uniq_i1,fname2,fname1,len(uniq_c2),uniq_c2,fname2,fname1,len(uniq_i2),uniq_i2))
  



class Experiment:
  def __init__(self, src, trg, method):
    self.src = src
    self.trg = trg
    self.method = method
    self.always = []
    self.settings = []
    self.results = {}
  def static(self, opt):
    #option to always use
    self.always = opt.split()
  def dynamic(self, opt, *valLists):
    self.settings.append((opt,valLists))
  def eachCLI(self):
    #getter = lambda n: lambda t: t[n]
    if self.settings == []:
      yield (self.always,[])
    else:
      for s,args in self.settings:
        for opts in zip(*args):
          yield (self.always + s.format(*opts).split(), opts)
  def storeResult(self,k,v):
    self.results[k] = v

def myExec(s):
    import subprocess as sp
    if type(s) == str:
      #print("Would have executed:\n{}".format(s))
      s = s.split()
      #return "{}"
    else:
      #print("Would have executed:\n{}".format(' '.join(s)))
      #return "{}"
      pass

    #print("Running: " + ' '.join(s))
    ret = sp.check_output(s).decode('utf-8')
    #print("Returning: " + ret)
    return ret

def sbatch(cmd, name):
  #make temp sbatch file
  #fill it
  #put in module loads
  #put in cmd
  #submit, keep the which, keep cmd too?
  sfname = "{}.sbatch".format(name)
  with open(sfname, mode='w') as sf:
    sf.write("#!/bin/sh\n")
    sf.write("#SBATCH --mem-per-cpu=256000MB\n")
    sf.write("#SBATCH -t 120:00:00\n")
    sf.write("module load python3\n")
    sf.write(' '.join(cmd))
  print("Wrote to {}".format(sfname))
  sid = myExec("sbatch {}".format(sfname)).split()[-1]
  with open("{}-{}.which".format(name,sid),mode='w') as wf:
    wf.write("{}\n".format(sid))
    wf.write(' '.join(cmd))
    wf.write("\n")
  myExec("rm -f {}".format(sfname))


def countCorrect(fn):
  with open(fn,mode='r') as f:
    ls = f.readlines()
    c = 0.
    t = 0.
    for l in ls:
      if l.startswith("Correct:"):
        c += 1
      t += 1
    return c, t

def recoverResults(exps, OUTPUT):
  for e in exps:
    st = "{}-{}".format(e.src, e.trg)
    for c,opts in e.eachCLI():
      methodname = e.method.format(*opts)
      dev_f = "{}/{}/numerals/{}/{}.translation.dev.results".format(OUTPUT,st,methodname,st)
      test_f = "{}/{}/numerals/{}/{}.translation.test.split.results".format(OUTPUT,st,methodname,st)
      test_full_f = "{}/{}/numerals/{}/{}.translation.test.results".format(OUTPUT,st,methodname,st)
      dev_c, dev_t = countCorrect(dev_f)
      test_c, test_t = countCorrect(test_f)
      test_full_c, test_full_t = countCorrect(test_full_f)
      dev_r = "{:04.2f}%".format(dev_c/dev_t*100)
      test_r = "{:04.2f}%".format(test_c/test_t*100)
      test_full_r = "{:04.2f}%".format(test_full_c/test_full_t*100)
      if len(opts) > 0:
        e.storeResult(str(opts[0]),(dev_r,test_r,test_full_r))
      else:
        e.storeResult("-",(dev_r,test_r,test_full_r))

def run(parsed_args):
  import os.path
    #run the experiments
  itartetxe = Experiment('en', 'it', 'proposed')
  deartetxe = Experiment('en', 'de', 'proposed')
  fiartetxe = Experiment('en', 'fi', 'proposed')

  #params = [1,2,3,4,5,6,7,8,10,16,1000000]#[1,2,3,4,5,6,7,8,10,16,1000000]
  params = [1,7]

  it1gram = Experiment('en','it','1gram{}')
  it1gram.static('--orthographic_learn_n 1')
  it1gram.dynamic('--orthographic_learn {}', params)

  de1gram = Experiment('en','de','1gram{}')
  de1gram.static('--orthographic_learn_n 1')
  de1gram.dynamic('--orthographic_learn {}', params)

  fi1gram = Experiment('en','fi','1gram{}')
  fi1gram.static('--orthographic_learn_n 1')
  fi1gram.dynamic('--orthographic_learn {}', params)

  itsimMat = Experiment('en','it','simMat{}')
  itsimMat.dynamic('--orthographic_sim {}', params)

  desimMat = Experiment('en','de','simMat{}')
  desimMat.dynamic('--orthographic_sim {}', params)

  fisimMat = Experiment('en','fi','simMat{}')
  fisimMat.dynamic('--orthographic_sim {}', params)

  itboth = Experiment('en','it','combined_1gram{}_simMat{}')
  itboth.static('--orthographic_learn_n 1')
  itboth.dynamic('--orthographic_learn {} --orthographic_sim {}', [7], [1])

  deboth = Experiment('en','de','combined_1gram{}_simMat{}')
  deboth.static('--orthographic_learn_n 1')
  deboth.dynamic('--orthographic_learn {} --orthographic_sim {}', [7], [1])

  fiboth = Experiment('en','fi','combined_1gram{}_simMat{}')
  fiboth.static('--orthographic_learn_n 1')
  fiboth.dynamic('--orthographic_learn {} --orthographic_sim {}', [7], [1])

  exps_1gram = [it1gram, de1gram, fi1gram]
  exps_simMat = [itsimMat, desimMat, fisimMat]
  exps_art = [itartetxe, deartetxe, fiartetxe]
  exps_both = [itboth, deboth, fiboth]
  exps_both_defi = [deboth, fiboth]
  #exps = exps_1gram + exps_simMat
  #exps = exps_art
  #exps = exps_both
  exps = exps_both_defi

  DATA = 'data'
  OUTPUT = 'output/acl2017'
  
  barline = '--------------------------------------------------------------------------------'
  if parsed_args.results_only:
    recoverResults(exps, OUTPUT)
    print(recordResults(exps))
    return
  for exp in exps:
    src = exp.src
    trg = exp.trg
    st = "{}-{}".format(src,trg)
    print(barline)
    print(st)
    print(barline)
    embedding_dir = "{}/embeddings/unit-center".format(DATA)

    for c,opts in exp.eachCLI():
      methodname = exp.method.format(*opts)
      output_dir = "{}/{}-{}/numerals/{}".format(OUTPUT,src,trg,methodname)
      src_out_emb = "{}/{}.emb.txt".format(output_dir,src)
      trg_out_emb = "{}/{}.emb.txt".format(output_dir,trg)
      if os.path.exists(src_out_emb) and os.path.exists(trg_out_emb) and not parsed_args.force_remap:
        print("Found mapped embeddings for {}:{}; skipping mapping".format(st,methodname))
      elif parsed_args.disable_map:
        print("Missing mapped embeddings for {}:{}, but --disable_map option present; skipping".format(st,methodname))
      else:
        myExec("mkdir -p {}".format(output_dir))
        cmd = "python3 map_embeddings.py {}/{}.emb.txt {}/{}.emb.txt {}/{}.emb.txt {}/{}.emb.txt --self_learning --numerals --verbose".format(embedding_dir,src,embedding_dir,trg,output_dir,src,output_dir,trg).split() + c
        #myExec(cmd)
        sbatch(cmd,"{}_{}".format(st,methodname))

      if os.path.exists(src_out_emb) and os.path.exists(trg_out_emb):
        outputline = "  - {} | Translation".format(methodname)
        cmd_dev = "python3 eval_translation.py --dot -d {}/dictionaries/{}.dev.txt --output {}/{}/numerals/{}/{}.translation.dev.results {} {}".format(DATA,st,OUTPUT,st,methodname,st,src_out_emb,trg_out_emb)
        #| grep -Eo \':[^:]+%\' | tail -1 tr -d \'\\n\'
        cmd_test = "python3 eval_translation.py --dot -d {}/dictionaries/{}.test.split.txt --output {}/{}/numerals/{}/{}.translation.test.split.results {} {}".format(DATA,st,OUTPUT,st,methodname,st,src_out_emb,trg_out_emb)
        cmd_test_full = "python3 eval_translation.py --dot -d {}/dictionaries/{}.test.txt --output {}/{}/numerals/{}/{}.translation.test.results {} {}".format(DATA,st,OUTPUT,st,methodname,st,src_out_emb,trg_out_emb)
        dev_output = myExec(cmd_dev).split()[-1]
        test_output = myExec(cmd_test).split()[-1]
        test_full_output = myExec(cmd_test_full).split()[-1]
        print(outputline + " (Dev) " + dev_output)
        print(outputline + " (Test) " + test_output)
        print(outputline + " (Test Full) " + test_full_output)
        if len(opts) > 0:
          exp.storeResult(str(opts[0]),(dev_output,test_output,test_full_output))
        else:
          exp.storeResult("-",(dev_output,test_output,test_full_output))
      else:
        print("Missing mapped embeddings for {}_{}; skipping evaluation".format(st,methodname))
  #end for exp

  #TODO: data compilation
  #file for SM, file for 1G
  #row for each scale, column for scales, dev, test (both by lang!)
  r = recordResults(exps)
  print(r)


def recordResults(exps):
  from collections import defaultdict
  files = defaultdict(lambda:defaultdict(lambda:defaultdict(str)))

  def myKey(a):
    try:
      a = float(a)
    except:
      pass
    if type(a) == str:
      return 1000001
    else:
      return a

  for e in exps:
    fkey = "{}.data".format(e.method.replace('{}',''))
    d = files[fkey]
    devstr = "{}_dev".format(e.trg)
    teststr = "{}_test".format(e.trg)
    testfullstr = "{}_test_full".format(e.trg)
    d['Scale_Factor'][devstr] = devstr
    d['Scale_Factor'][teststr] = teststr
    d['Scale_Factor'][testfullstr] = testfullstr
    for k in e.results:
      try:
        k2 = "{:02.7f}".format(1.0/float(k))
      except:
        k2 = k
      d[k2][devstr] = e.results[k][0]
      d[k2][teststr] = e.results[k][1]
      d[k2][testfullstr] = e.results[k][2]


  for fn in files:
    with open(fn,mode='w') as f:
      d = files[fn]
      for r in sorted(d.keys(), key=myKey, reverse=True):
        s = str(r)
        for c in sorted(d[r].keys()):
          s += " " + d[r][c]
        f.write("{}\n".format(s))

  return files

def main():
  import sys
  parser = argparse.ArgumentParser(description='Useful functionality for investigating results')
  subs = parser.add_subparsers(help='various sub-functionalities',dest='cmd')
  #parser_idents = subs.add_parser('idents', help='count identities')
  #parser_idents.add_argument('d', help='dictionary to count in')
  #parser.add_argument('-o', help='the output file')
  parser.add_argument('--idents', help='count identities in given dictionary file')
  #parser.add_argument('--overlap', action='store_true', help='determine overlap between two results files')
  parse_run = subs.add_parser('run',help='run experiments')
  parse_run.add_argument('--force_remap', action='store_true', help='force embeddings to be re-mapped')
  parse_run.add_argument('--disable_map', action='store_true', help='skip mapping; skips evaluation for unmapped tasks')
  parse_run.add_argument('--results_only', action='store_true', help='skip mapping and evaluation, just compile results')
  parse_overlap = subs.add_parser('overlap', help='determine overlap between two results files')
  parse_overlap.add_argument('f1', help='the first input file')
  parse_overlap.add_argument('f2', nargs='?',help='the second input file')
  parse_overlap.add_argument('--investigate', action='store_true',help='look at correct/incorrect in results file')


  args = parser.parse_args()

  #if args.o:
  #  print("Redirecting output...")
  #  sys.stdout = open(args.o,encoding='utf-8',mode='w',errors='surrogateescape')


  if args.idents:
    idents(args.idents)
  elif args.cmd == 'overlap':
    overlap(args)#args.f1, args.f2)
  elif args.cmd == 'run':
    run(args)
  else:
    print("No option selected! Exiting...")
    

if __name__ == "__main__":
  main()
      

