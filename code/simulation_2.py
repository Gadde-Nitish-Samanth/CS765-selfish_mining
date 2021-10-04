import numpy as np
import simpy
from networkgen import *
from models import *
from datetime import datetime

# used the libraries simpy(for simulation) and numpy

#input---------------------------------------------------------------------------------------------------------
n = int(input("Enter the number of nodes(n): "))
z = 50
T_tx = int(input("Enter the mean interarrival time of transactions(T_tx): "))
percent_high_cpu = int(input("Enter the percent of High CPU nodes(percent_high_cpu): "))
B_Tx = int(input("Enter block interarrival time(B_Tx)(in sec): "))

# Setup--------------------------------------------------------------------------------------------------------

# Global Variables
env = simpy.Environment()
stop_time = 500
all_balance=20 # initial balance of all users
invalid_ratio = 0.1
total_hash_power = 0 

node_list=[]
weights = []

# nodes creation
for i in range(n):
	speed = np.random.uniform()
	cpu = np.random.uniform()
	if speed<(z/100):
		speed = 0
	else:
		speed=1
	if cpu<(percent_high_cpu/100):
		hash_power = 2
	else:
		hash_power = 1
	total_hash_power = total_hash_power+hash_power

	genesis_block = Block('gen','none',[],0,'none')
	node = Node(i,speed,genesis_block,genesis_block,genesis_block,hash_power,0)
	node_list.append(node)
	weights.append(1+9*speed)

selfish_node=0
for i in node_list:
	if i.speed ==1:
		i.selfish=1
		selfish_node=i.id
		break

#network generation
adj = networkgen(n,2,weights)
for i in range(n):
	for j in range(i+1):
		if(adj[i][j]==1):
			r_ij = np.random.uniform(10,500)
			if(node_list[i].speed==1 and node_list[j].speed==1):
				c_ij=100
			else:
				c_ij=5
			connect_j = link(j,r_ij,c_ij)
			connect_i = link(i,r_ij,c_ij)
			node_list[i].peers.append(connect_j)
			node_list[j].peers.append(connect_i)

# helper functions-----------------------------------------------------------------------------------------------------

def get_balance(itr_blk): # returns list of balance of nodes from using itr_node to gen blockchain 
	calc_bal = []
	for i in range(n):
		calc_bal.append(all_balance)
	while itr_blk!='none':
		trxns = itr_blk.trxn_list
		for t in trxns:
			if t.payer!=-1:
				calc_bal[t.payer] = calc_bal[t.payer]-t.coins
			calc_bal[t.payee] = calc_bal[t.payee]+t.coins
		itr_blk = itr_blk.parent_ptr
	return calc_bal

def get_trxns(itr_blk): # returns all trxns in blocks from genesis block to itr_node
	all_trxns = []
	while itr_blk!='none':
		all_trxns.extend(itr_blk.trxn_list)
		itr_blk = itr_blk.parent_ptr
	return all_trxns

def get_parent(parent_id,check_blk): # returns parent blk if present in the tree from check_blk or returns 0
	if(check_blk.blk_id == parent_id):
		return check_blk
	elif (len(check_blk.child_ptr_list)==0):
		return 0
	else:
		for child in check_blk.child_ptr_list:
			temp = get_parent(parent_id,child)
			if temp!=0:
				return temp
		return 0 

def is_valid(node_id,blk): # returns parent_blk if valid or returns 0
	parent = get_parent(blk.parent_id,node_list[node_id].genesis_blk)
	if parent!=0: # has parent
		done_trxns = get_trxns(parent)
		repeated = [x for x in blk.trxn_list if x in done_trxns]
		if len(repeated)>0:
			return 0 # has a trxn from blockchain
		for child in parent.child_ptr_list:
			if blk.blk_id == child.blk_id:
				return 0 # already in blockchain
		calc_bal = get_balance(parent)
		for t in blk.trxn_list:
			if t.payer!=-1:
				calc_bal[t.payer] = calc_bal[t.payer]-t.coins
			calc_bal[t.payee] = calc_bal[t.payee]+t.coins
		valid = True
		for i in calc_bal:
			if i<0:
				valid = False
		if valid: # valid
			return parent
		else:
			return 0 # balance goes negative
	return 0 # no parent

def child_num(node_id,parent_id): # returns the number of childs of parent
	parent = get_parent(parent_id,node_list[node_id].genesis_blk)
	return len(parent.child_ptr_list)

def add_orphans(node_id,blk): # adds the orphan blocks to blockchain
	for child_blk in node_list[node_id].orphan_blocks:
		if(child_blk.parent_id==blk.blk_id):
			child_blk.level = blk.level+1
			child_blk.parent_ptr = blk
			blk.child_ptr_list.append(child_blk)
			if(child_blk.level>node_list[node_id].mining_blk.level):
				node_list[node_id].mining_blk = blk
				# print('longest chain changed for node %d' % node_id)
				create_blk(node_id)
			node_list[node_id].orphan_blocks.remove(child_blk)
			add_orphans(node_id,child_blk)


# trxn generation,broadcasting and routing----------------------------------------------------------------------
def route_trxn(node_id,trxn,lat,f_id):
	yield env.timeout(lat)
	# print('Node %d : got packet %s from %d at %f' % (node_id,trxn.id,f_id,env.now))
	present = False
	for i in node_list[node_id].trxn_pool:
		if(i.id == trxn.id):
			present=True
	if(not present):
		node_list[node_id].trxn_pool.append(trxn)
		for l in node_list[node_id].peers:
			if(l.j!=f_id):
				d_ij = np.random.exponential(96/l.c_ij)
				lat = (l.r_ij+d_ij+8/l.c_ij)*(0.001)
				# print('routing trxn %s to %d with delay = %f' % (trxn.id,l.j,lat))
				env.process(route_trxn(l.j,trxn,lat,node_id))

def broadcast_trxn(node_id,trxn):
	for l in node_list[node_id].peers:
		d_ij = np.random.exponential(96/l.c_ij)
		lat = (l.r_ij+ d_ij+ 8/l.c_ij)*(0.001)
		# print('broadcasting trxn %s to %d with delay = %f' % (trxn.id,l.j,lat))
		env.process(route_trxn(l.j,trxn,lat,node_id))

def create_trxn(node_id):
	while True:
		yield env.timeout(np.random.exponential(T_tx))
		temp = get_balance(node_list[node_id].mining_blk)
		bal = temp[node_id]
		if bal>0:
			vendor = random.randint(0,n-2)
			if(vendor>=node_id):
				vendor=vendor+1
			valid = np.random.uniform()
			pay=0
			if valid<invalid_ratio:
				pay = bal+10000
			else:
				pay = random.randint(1,bal)

			node_list[node_id].trxn_cnt = node_list[node_id].trxn_cnt+1
			trxn_id = str(node_id)+"_"+str(node_list[node_id].trxn_cnt)
			str_trxn = str(trxn_id)+": "+str(node_id)+" pays "+str(vendor)+" "+str(pay)+" coins"
			# print(str_trxn + ' at %f' % env.now)
			real_trxn = Trxn(trxn_id,node_id,vendor,pay)
			broadcast_trxn(node_id,real_trxn)
			node_list[node_id].trxn_pool.append(real_trxn)

# block generation,broadcasting and routing----------------------------------------------------------------------------

def add_orphans_public(node_id,blk):
	for child_blk in node_list[node_id].orphan_blocks:
		if(child_blk.parent_id==blk.blk_id):
			child_blk.level = blk.level+1
			child_blk.parent_ptr = blk
			blk.child_ptr_list.append(child_blk)
			# print("selfish node %d: added %s to blockchain" %(node_id,blk.blk_id))
			if(child_blk.level>node_list[node_id].public_mining_blk.level):
				node_list[node_id].public_mining_blk = blk
				# print('longest chain changed for node %d' % node_id)
			node_list[node_id].orphan_blocks.remove(child_blk)
			add_orphans_public(node_id,child_blk)

def send_all(node_id,prev_lead):
	blk = node_list[node_id].mining_blk
	while prev_lead>0:
		for l in node_list[node_id].peers:
			d_ij = np.random.exponential(96/l.c_ij)
			blk_size= len(blk.trxn_list)
			lat = (l.r_ij+ d_ij+ 8*blk_size/l.c_ij)*(0.001)
			# print('to %d with delay = %f' % (l.j,lat))
			env.process(route_blk(l.j,blk,lat,node_id))
		prev_lead=prev_lead-1
		blk = blk.parent_ptr


def send_blks(node_id,new_lead,prev_lead):
	blk = node_list[node_id].mining_blk
	lead=1
	while (lead <= prev_lead):
		if lead > new_lead:
			for l in node_list[node_id].peers:
				d_ij = np.random.exponential(96/l.c_ij)
				blk_size= len(blk.trxn_list)
				lat = (l.r_ij+ d_ij+ 8*blk_size/l.c_ij)*(0.001)
				# print('to %d with delay = %f' % (l.j,lat))
				env.process(route_blk(l.j,blk,lat,node_id))
		blk  = blk.parent_ptr
		lead = lead+1 

def route_blk(node_id,blk,lat,f_id): #checked
	yield env.timeout(lat)
	# print('Node %d : got blk %s from %d at %f' % (node_id,blk.blk_id,f_id,env.now))
	parent = is_valid(node_id,blk)

	if(parent!=0):
		prev_lead = node_list[node_id].mining_blk.level - node_list[node_id].public_mining_blk.level
		blk = Block(blk.blk_id,parent.blk_id,blk.trxn_list,parent.level+1,parent)
		parent.child_ptr_list.append(blk)
		node_list[node_id].timestamp_list.append([blk.blk_id,blk.level,env.now,blk.parent_id])
		# print('childs of parent = %d' %child_num(node_id,blk.parent_id))
		if node_list[node_id].selfish==0:
			for l in node_list[node_id].peers:
				if(l.j!=f_id):
					d_ij = np.random.exponential(96/l.c_ij)
					blk_size= len(blk.trxn_list)
					lat = (l.r_ij+d_ij+8*blk_size/l.c_ij)*(0.001)
					# print('routing block %s to %d with delay = %f' % (blk.blk_id,l.j,lat))
					env.process(route_blk(l.j,blk,lat,node_id)) 
			if blk.level > node_list[node_id].mining_blk.level:
				node_list[node_id].mining_blk = blk
				# print('longest chain changed for node %d' % node_id)
				create_blk(node_id)
			add_orphans(node_id,blk)
		else:
			# to do send_all(), send_blks
			# print("selfish node %d: added %s to blockchain" %(node_id,blk.blk_id))
			if blk.level > node_list[node_id].public_mining_blk.level:
				node_list[node_id].public_mining_blk = blk
			add_orphans_public(node_id,blk) # add orphans and update public_mining_blk
			new_lead = node_list[node_id].mining_blk.level - node_list[node_id].public_mining_blk.level
			if new_lead<0:
				node_list[node_id].mining_blk = node_list[node_id].public_mining_blk
				node_list[node_id].private_chain_length=0
				create_blk(node_id)
			else:
				send_blks(node_id,new_lead,prev_lead)

	else:
		temp = get_parent(blk.parent_id,node_list[node_id].genesis_blk)
		if(temp==0):
			blk = Block(blk.blk_id,blk.parent_id,blk.trxn_list,0,'none')
			node_list[node_id].orphan_blocks.append(blk)
			node_list[node_id].timestamp_list.append([blk.blk_id,blk.level,env.now,blk.parent_id])


def broadcast_blk(node_id,blk,valid): #checked
	yield env.timeout(np.random.exponential()*(B_Tx*total_hash_power/node_list[node_id].hash_power))
	if node_list[node_id].mining_blk.blk_id == blk.parent_id:
		prev_lead = node_list[node_id].mining_blk.level - node_list[node_id].public_mining_blk.level
		if valid==1:
			node_list[node_id].mining_blk.child_ptr_list.append(blk)
			node_list[node_id].mining_blk = blk
			node_list[node_id].timestamp_list.append([blk.blk_id,blk.level,env.now,blk.parent_id])
		# print('longest chain changed for node %d' % node_id)
		# print('childs of parent = %d' %child_num(node_id,blk.parent_id))
		# print("broadcasting block %s at %f" %(blk.blk_id,env.now))
		if node_list[node_id].selfish==0:
			for l in node_list[node_id].peers:
				d_ij = np.random.exponential(96/l.c_ij)
				blk_size= len(blk.trxn_list)
				lat = (l.r_ij+ d_ij+ 8*blk_size/l.c_ij)*(0.001)
				# print('to %d with delay = %f' % (l.j,lat))
				env.process(route_blk(l.j,blk,lat,node_id))
		else:
			node_list[node_id].private_chain_length = node_list[node_id].private_chain_length+1
			# print("selfish node%d: added %s to private chain" % (node_id,blk.blk_id))
			# if prev_lead==0 and node_list[node_id].private_chain_length==2:
			# 	# print("selfish node %d: broadcasting block %s since in state 0`" % (node_id,blk.blk_id))
			# 	for l in node_list[node_id].peers:
			# 		d_ij = np.random.exponential(96/l.c_ij)
			# 		blk_size= len(blk.trxn_list)
			# 		lat = (l.r_ij+ d_ij+ 8*blk_size/l.c_ij)*(0.001)
			# 		# print('to %d with delay = %f' % (l.j,lat))
			# 		env.process(route_blk(l.j,blk,lat,node_id))
			# 	node_list[node_id].private_chain_length=0
			# 	node_list[node_id].public_mining_blk=node_list[node_id].mining_blk

		create_blk(node_id)

def create_blk(node_id): # checked
		node_list[node_id].blk_cnt = node_list[node_id].blk_cnt+1
		blk_id = 'b'+str(node_id)+'_'+str(node_list[node_id].blk_cnt)
		
		parent_id = node_list[node_id].mining_blk.blk_id
		
		trxn_list = []# get the trxn list
		node_list[node_id].trxn_cnt =node_list[node_id].trxn_cnt+1
		mining_trxnid = str(node_id)+'_'+str(node_list[node_id].trxn_cnt)
		trxn_list.append(Trxn(mining_trxnid,-1,node_id,50))
		# add other trxns
		if node_list[node_id].selfish==1:
			# to do 
			valid=1
			calc_bal = get_balance(node_list[node_id].mining_blk)
			done_trxns = get_trxns(node_list[node_id].mining_blk)
			useful_trxns = [ele for ele in node_list[node_id].trxn_pool if ele not in done_trxns]
			for t in useful_trxns:
				if(((calc_bal[t.payer]-t.coins)>=0) and len(trxn_list)<1000):
					trxn_list.append(t)
					calc_bal[t.payer] = calc_bal[t.payer]-t.coins
					calc_bal[t.payee] = calc_bal[t.payee]+t.coins
			# print("selfish node : creating %s at %f" %(blk_id,env.now))

		else:
			valid = np.random.uniform()
			if valid<invalid_ratio:
				if len(node_list[node_id].trxn_pool)<1000:
					trxn_list.extend(node_list[node_id].trxn_pool)
				else:
					trxn_list.extend(node_list[node_id].trxn_pool[-999:])
				valid=0
				# print('invalid block with id %s created' %blk_id)

			else:
				valid=1
				calc_bal = get_balance(node_list[node_id].mining_blk)
				done_trxns = get_trxns(node_list[node_id].mining_blk)
				useful_trxns = [ele for ele in node_list[node_id].trxn_pool if ele not in done_trxns]
				for t in useful_trxns:
					if(((calc_bal[t.payer]-t.coins)>=0) and len(trxn_list)<1000):
						trxn_list.append(t)
						calc_bal[t.payer] = calc_bal[t.payer]-t.coins
						calc_bal[t.payee] = calc_bal[t.payee]+t.coins

		level = node_list[node_id].mining_blk.level+1
		parent_ptr = node_list[node_id].mining_blk
		new_blk = Block(blk_id,parent_id,trxn_list,level,parent_ptr)

		# print('Block %s is created at t = %f with num_trxns = %d' % (blk_id,env.now,len(trxn_list)))
		# print('parent_blk_id = %s' %parent_id)
		# print('trxn list:')
		# for i in trxn_list:
		# 	print(i.id)
		# print('level:%d' %level)
		
		env.process(broadcast_blk(node_id,new_blk,valid))


# Simulation---------------------------------------------------------------------------------------------------

for i in node_list:
	env.process(create_trxn(i.id))
	create_blk(i.id)

env.run(until=stop_time)

# writing treefiles
for node in node_list:
	filename = 'treefile'+str(node.id)+'.txt'
	file = open(filename,'w')
	line=''
	for info in node.timestamp_list:
		line = line+str(info[0])+','+str(info[1])+','+str(info[2])+','+str(info[3])+'\n'
	file.write(line)
	file.close()

#extras--------------------------------------------------------------------------------------------------------
## ratio for blocks

# def get_num_blks(blk):
# 	num = np.zeros(n)
# 	while(blk.blk_id!='gen'):
# 		id = blk.blk_id
# 		split = id.split('_')
# 		node = split[0]
# 		node= int(node[1:])
# 		num[node]=num[node]+1
# 		blk = blk.parent_ptr
# 	return num


# last_blk = node_list[0].mining_blk
# num=get_num_blks(last_blk)
# sum1=0
# sum2=0
# sum3=0
# sum4=0
# num1=0
# num2=0
# num3=0
# num4=0
# for i in range(n):
# 	if (node_list[i].speed==0):
# 		if(node_list[i].hash_power==1):
# 			num1=num1+1
# 			sum1=sum1+num[i]/node_list[i].blk_cnt
# 		else:
# 			num2=num2+1
# 			sum2=sum2+num[i]/node_list[i].blk_cnt
# 	else:
# 		if(node_list[i].hash_power==1):
# 			num3=num3+1
# 			sum3=sum3+num[i]/node_list[i].blk_cnt
# 		else:
# 			num4=num4+1
# 			sum4=sum4+num[i]/node_list[i].blk_cnt
# print(sum1/num1,sum2/num2,sum3/num3,sum4/num4)

# printing selfish nodes
print(selfish_node)

# printing info for visualization
num=0
def print_tree(blk,parent_num):
	global num
	num=num+1
	print(num,parent_num,blk.blk_id)
	blk_num = num
	for child in blk.child_ptr_list:
		print_tree(child,blk_num)

gen = node_list[selfish_node].genesis_blk
print("selfish node:")
print_tree(gen,"NaN")
selfish_node = (selfish_node+1)%n
print("normal node:")
gen = node_list[selfish_node].genesis_blk
print_tree(gen,"NaN")

# # list of length of branches
# lst = []
# def get_length(blk):
# 	global lst
# 	if len(blk.child_ptr_list)==0:
# 		lst.append(blk.level)
# 	for child in blk.child_ptr_list:
# 		get_length(child)

# gen = node_list[0].genesis_blk
# get_length(gen)
# print(lst)

# #printing number of transactions in a block:
# print(len(node_list[0].mining_blk.trxn_list))

# #printing number of blocks in blockchains:
# print(node_list[0].mining_blk.level)

# done -----------------------------------------------------------------------------------------------