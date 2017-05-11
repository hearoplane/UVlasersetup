# 3D zig-zag scan pattern generator with arbitrary fast axis

N = (3,5,7)
axis_order = (0,1,2)

def ijk_generator(axis_order, dims):
	
	ax0, ax1, ax2 = axis_order
	
	for i_ax0 in range( dims[ax0] ):
		zig_or_zag0 = (1,-1)[i_ax0 % 2]
		for i_ax1 in range( dims[ax1] )[::zig_or_zag0]:
			zig_or_zag1 = (1,-1)[(i_ax0+i_ax1) % 2]
			for i_ax2 in range( dims[ax2] )[::zig_or_zag1]:
			
				ijk = [0,0,0]
				ijk[ax0] = i_ax0
				ijk[ax1] = i_ax1
				ijk[ax2] = i_ax2
				
				yield tuple(ijk)
	return
	
	
for ijk in ijk_generator(axis_order, N):
	print ijk, sum(ijk)