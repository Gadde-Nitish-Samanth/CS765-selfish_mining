### tree diagram with gnuplot
reset session

#ID  Parent   Name
$Data <<EOD
1 NaN gen
2 1 b0_1
3 2 b1_2
4 2 b0_3
5 4 b0_4
6 5 b2_4
7 6 b4_5
8 7 b1_6
9 7 b2_6
10 9 b3_7
11 10 b4_8
12 11 b4_9
13 12 b1_10
14 13 b4_12
15 14 b3_12
16 15 b3_13
17 16 b1_14
18 16 b2_16
19 18 b3_15
20 19 b2_18
21 20 b2_19
22 21 b3_18
23 22 b0_20
24 23 b3_20
25 24 b2_23
26 25 b3_22
27 26 b1_23
28 26 b3_23
29 28 b2_26
30 29 b2_27
31 30 b2_28
32 31 b1_27
33 31 b3_29
34 33 b0_29
35 34 b2_31
36 35 b0_31
37 36 b2_33
38 37 b0_33
39 38 b1_33
40 38 b2_35
41 40 b0_35
42 41 b2_37
43 42 b2_38
44 12 b0_11

EOD

# put datablock into strings
IDs = Parents = Names = ''
set table $Dummy
    plot $Data u (IDs = IDs.strcol(1).' '): \
                 (Parents = Parents.strcol(2).' '): \
                 (Names = Names.strcol(3).' ') w table
unset table

# Top node has no parent ID 'NaN'
Start(n) = int(sum [i=1:words(Parents)] (word(Parents,i) eq 'NaN' ? int(word(IDs,i)) : 0))

# get list index by ID
ItemIdx(s,n) = n == n ? (tmp=NaN, sum [i=1:words(s)] ((word(s,i)) == n ? (tmp=i,0) : 0), tmp) : NaN

# get parent of ID n
Parent(n) = word(Parents,ItemIdx(IDs,n))

# get level of ID n, recursive function
Level(n) = n == n ? Parent(n)>0 ? Level(Parent(n))-1 : 0 : NaN

# get number of children of ID n
ChildCount(n) = int(sum [i=1:words(Parents)] (word(Parents,i)==n))

# Create child list of ID n
ChildList(n) = (Ch = ' ', sum [i=1:words(IDs)] (word(Parents,i)==n ? (Ch = Ch.word(IDs,i).' ',1) : (Ch,0) ), Ch )

# m-th child of ID n
Child(n,m) = word(ChildList(n),m)

# List of leaves, recursive function
LeafList(n) = (LL='', ChildCount(n)==0 ? LL=LL.n.' ' : sum [i=1:ChildCount(n)] (LL=LL.LeafList(Child(n,i)), 0),LL)

# create list of all leaves
LeafAll = LeafList(Start(0))

# get x-position of ID n, recursive function
XPos(n) = ChildCount(n) == 0 ? ItemIdx(LeafAll,n) : (sum [i=1:ChildCount(n)] (XPos(Child(n,i))))/(ChildCount(n))

# create the tree datablock for plotting
set print $Tree
    do for [j=1:words(IDs)] {
        n = int(word(IDs,j))
        print sprintf("% 3d % 7.2f % 4d % 5s", n, XPos(n), Level(n), word(Names,j))
    }
set print
print $Tree

# get x and y distance from ID n to its parent
dx(n) = XPos(Parent(int(n))) - XPos(int(n))
dy(n) = Level(Parent(int(n))) - Level(int(n))

unset border
unset tics
set offsets 0.25, 0.25, 0.25, 0.25

plot $Tree u 2:3:(dx($1)):(dy($1)) w vec nohead ls -1 not,\
        '' u 2:3 w p pt 7 ps 6 lc rgb 0xccffcc not, \
        '' u 2:3 w p pt 6 ps 6 lw 1.5 lc rgb "black" not, \
        '' u 2:3:4 w labels offset 0,0.1 center not
### end of code