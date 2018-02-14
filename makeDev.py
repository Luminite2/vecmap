def main():
  import argparse
  parser = argparse.ArgumentParser(description="split test data")
  parser.add_argument('full')
  parser.add_argument('dev')
  parser.add_argument('split')
  args = parser.parse_args()

  with open(args.full, encoding='utf-8', errors='surrogateescape') as f:
    ls = f.readlines()
  with open(args.dev, mode='w',encoding='utf-8', errors='surrogateescape') as d:
    with open(args.split, mode='w', encoding='utf-8', errors='surrogateescape') as s:
      #some source words listed multiple times; all multi-lists should appear in same file
      #alternate assignment of FIRST-OCCURENCE source words; if already seen, put it in matching file
      devs = set()
      splits = set()
      for l in ls:
        src = l.split()[0]
        if src in devs:
          d.write(l)
        elif src in splits:
          s.write(l)
        elif len(devs) >= len(splits):
          splits.add(src)
          s.write(l)
        else:
          devs.add(src)
          d.write(l)


if __name__ == "__main__":
  main()
