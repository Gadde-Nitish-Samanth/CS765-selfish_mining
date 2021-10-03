import numpy as np

def networkgen(n,m,w):

    adj = np.zeros((n,n))
    count = np.zeros((n)) 

    for i in range(m):
        adj[0][i+1] = 1
        adj[i+1][0] = 1
        count[0] = count[0]+1
        count[i+1] = count[i+1]+1

    for i in range(1,n):
        s = np.sum(w*count)
        t = [val/s for ind, val in enumerate(w*count)]

        for j in range(1,n):
            t[j] = t[j] + t[j-1]
        
        t = [0]+ t

        for k in range(m):
            p = np.random.uniform(0,1);

            for j in range(1,n+1):
                if j-1<i and adj[i][j-1]==0 and t[j-1]<=p and p < t[j]:
                    adj[i][j-1] = 1
                    adj[j-1][i] = 1
                    count[i] = count[i]+1
                    count[j-1] = count[j-1]+1
                    break

    print(adj)
    # print(count)
    return adj