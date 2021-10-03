### tree diagram with gnuplot
reset session

#ID  Parent   Name
$Data <<EOD
34 NaN gen
35 34 b3_1
36 35 b2_2
37 36 b1_3
38 37 b4_4
39 38 b4_5
40 39 b4_6
41 40 b3_7
42 41 b3_9
43 42 b3_10
44 43 b4_10
45 44 b4_11
46 45 b2_14
47 46 b1_13
48 47 b3_15
49 48 b2_17
50 49 b1_17
51 50 b2_19
52 51 b3_19
53 52 b2_21
54 53 b2_22
55 54 b4_21
56 55 b2_24
57 56 b3_24

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