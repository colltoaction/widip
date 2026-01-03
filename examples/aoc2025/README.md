# Advent of Code 2025

Solutions pipelines for [AoC 2025](https://adventofcode.com/2025) implemented in widip YAML.

## Day 1-1

```bash
cat examples/aoc2025/1-1.input \
  | tr 'LR' '-+' \
  | awk 'BEGIN {sum=50} {sum = (sum+$1+100)%100; print sum}' \
  | grep -c '^0$'
# Expected: 1147
```

<img src="1-1.shell.svg" width="320">

## Day 1-2

```bash
cat examples/aoc2025/1-1.input \
  | tr 'LR' '-+' \
  | awk 'BEGIN { AT = 50 }
    {
      if ($1<0) {DIR = -1} else {DIR = 1}
      TICKS = DIR*$1
      while (TICKS-->0) {
        HITS += (AT+=DIR)%100 == 0
      }
    }
    END { print HITS }'
# Expected: 6789
```

<img src="1-2.shell.svg" width="320">

## Day 2-1

```bash
cat examples/aoc2025/2-1.input \
  | tr ',-' ' ' \
  | xargs -n2 seq \
  | grep -E '^(.+)\1{1}$' \
  | awk -f examples/aoc2025/sum.awk
# Expected: 13108371860
```

<img src="2-1.shell.svg" width="400">

## Day 2-2

```bash
cat examples/aoc2025/2-1.input \
  | tr ',-' ' ' \
  | xargs -n2 seq \
  | grep -E '^(.+)\1{1,}$' \
  | awk -f examples/aoc2025/sum.awk
# Expected: 22471660255
```

<img src="2-2.shell.svg" width="400">

## Day 3-1

```bash
cat examples/aoc2025/3-1.input \
  | awk '{
      l = length($0)
      maxn = 0
      for (i=1; i<l; i+=1) {
        for (j=i+1; j<=l; j+=1) {
          n = int(substr($0, i, 1)substr($0, j, 1))
          if (n > maxn) maxn = n
        }
      }
      print maxn
    }' \
  | awk -f examples/aoc2025/sum.awk
# Expected: 17324
```

<img src="3-1.shell.svg" width="320">