from ngsolve.fem import *
from ngsolve.comp import *
from ngsolve.solve import *
from ngsolve.ngstd import *
from ngsolve.la import *


#import numpy as np

from math import sqrt

from time import sleep

#import libngsxfem_py.xfem as xfem                                 
from libngsxfem_py.xfem import *

material_params_artificial ={"eta" : [1,1], 
                             "rho" : [0.1,0], 
                             "g" : 9.81, 
                             "sigma" : 0.1}

material_params_water_butanol = {"eta" : [0.001388,0.003281], 
                                 "rho" : [986.506,845.442], 
                                 "g" : 9.81, 
                                 "sigma" : 0.00163}

solver_params_water_butanol_default ={ "lsetorder" : 2,
                                       "velorder" : 2, 
                                       "ref_space" : 1, 
                                       "dt" : 0.0001, 
                                       "timesteps" : 200,
                                       "relvelx" : 0,
                                       "relvely" : -0.1,
                                       "initial_cond" : "zero"
                                     }


# from libxfem import *
class Levelset:
    def __init__(self, mesh, init_lset, order=1):
        self.fes = FESpace ("HDG", mesh, order=order,
                            flags = {"dirichlet" : [1,2,3,4]} )
        self.fes.Update()
        self.gf = GridFunction(self.fes)
        self.gf.Update()
        self.gf.components[0].Set(init_lset)
        self.coef = GFCoeff(self.gf)

        self.cont_fes = FESpace ("h1ho", mesh, order=order)
        self.cont_fes.Update()
        self.cont_gf = GridFunction(self.cont_fes)
        self.cont_gf.Update()
        self.cont_gf.Set(init_lset)
        self.cont_coef = GFCoeff(self.cont_gf)

class VelocityPressure:
    def __init__(self, mesh, lset,
                 init_vals=[ConstantCF(0), ConstantCF(0)], 
                 dirichlet_vel = [1,2,3,4],
                 dirichlet_vel_vals = [ConstantCF(0),ConstantCF(0)],
                 ref_space = 1,
                 order=1):
        self.fes = FESpace ("xstokes", mesh=mesh, order=order, 
                            flags = {"dirichlet_vel" : dirichlet_vel, "empty_vel" : True, 
                                     "dgjumps" : False, "ref_space" : ref_space})

        CastToXStokesFESpace(self.fes).SetLevelSet(lset.cont_coef)
        self.fes.Update()

        self.gf = GridFunction(self.fes)
        self.gf.Update()

        self.gf.components[0].components[0].Set(coefficient = init_vals[0], boundary = False)
        self.gf.components[1].components[0].Set(coefficient = init_vals[1], boundary = False)

        self.gf.components[0].components[0].Set(coefficient = dirichlet_vel_vals[0], boundary = True)
        self.gf.components[1].components[0].Set(coefficient = dirichlet_vel_vals[1], boundary = True)

        self.coef = [GFCoeff(self.gf.components[0]), GFCoeff(self.gf.components[1])]
    
class LevelsetSolver:
    def __init__(self, lset, velpre, dt):
        self.dt = dt
        self.lset = lset 

        self.f = LinearForm (lset.fes)
        lfi_inner = LFI (name = "source", dim = 2,  coef = [GFCoeff(lset.gf)])
        lfi_block = CompoundLFI ( lfi = lfi_inner, comp = 0 )
        self.f.Add (lfi_block)
        
        self.a = BilinearForm (lset.fes, flags = { "symmetric" : False })
        bfi_inner = BFI (name = "mass", dim = 2,  coef = [ConstantCF(1.0/self.dt)])
        bfi_block = CompoundBFI (bfi = bfi_inner, comp = 0 )
        self.a.Add (bfi_block)

        self.a.Add (BFI (name = "HDG_convection", dim = 2, coef = velpre.coef))
        
        self.c = Preconditioner (self.a, "direct", { "inverse" : "pardiso" })

        # lset project: definition of (bi-) and linear forms

        self.proj_f = LinearForm (lset.cont_fes)
        self.proj_f.Add (LFI (name = "source", dim = 2,  coef = [GFCoeff(lset.gf)]))
        
        self.proj_a = BilinearForm (lset.cont_fes, flags = { "symmetric" : True })
        self.proj_a.Add (BFI (name = "mass", dim = 2,  coef = [ConstantCF(1)]))

        self.proj_c = Preconditioner (self.proj_a, "direct", { "inverse" : "pardiso" })

        self.proj_a.Assemble()
        self.proj_c.Update()

    def Update(self, keep_old = False):
        if (keep_old == False):
            self.f.Assemble()
        self.a.Assemble()

    def Solve(self, printrates = False, printrates_proj = False):
        self.c.Update()
        solver = CGSolver (self.a.mat, self.c.mat, printrates=printrates)
        self.lset.gf.vec.data = 1.0/self.dt * solver * self.f.vec
        self.proj_f.Assemble()
        solver_proj = CGSolver (self.proj_a.mat, self.proj_c.mat, printrates=printrates_proj)
        self.lset.cont_gf.vec.data = solver_proj * self.proj_f.vec
        
class StokesSolver:
    def __init__(self, velpre, lset, dt,
                 params = {"eta" : [1,1], "rho" : [0.1,0], "g" : 9.81, "sigma" : 0.1},
                 initial = False
                 ):
        self.initial = initial
        self.dt = dt
        self.velpre = velpre
        self.f = LinearForm (self.velpre.fes)
        lfi_grav_inner = LFI (name = "xsource", dim = 2, 
                              coef = [ConstantCF(params["rho"][0]*params["g"]), 
                                      ConstantCF(params["rho"][1]*params["g"])])
        self.f.Add (CompoundLFI ( lfi = lfi_grav_inner, comp=1))
        self.f.Add (LFI (name = "xmodLBmeancurv", dim = 2, 
                         coef = [ConstantCF(params["sigma"]), lset.coef]))

        self.a = BilinearForm (self.velpre.fes, flags = { "symmetric" : True })
        self.a.Add (BFI (name = "xstokes", dim = 2, coef = [ConstantCF(params["eta"][0]), 
                                                       ConstantCF(params["eta"][1])]))
        self.c = Preconditioner (self.a, "direct", { "inverse" : "pardiso" })


        if (self.initial == False):
            self.f_old = LinearForm (self.velpre.fes)

            #todo add mass and source term to stokes
            lfi_inner_x = LFI (name = "xsource", dim = 2,  
                               coef = [self.velpre.coef[0],self.velpre.coef[0]])
            lfi_block_x = CompoundLFI (lfi = lfi_inner_x, comp = 0 )
            self.f_old.Add (lfi_block_x)
            
            lfi_inner_y = LFI (name = "xsource", dim = 2,  
                               coef = [self.velpre.coef[1],self.velpre.coef[1]])
            lfi_block_y = CompoundLFI (lfi = lfi_inner_y, comp = 1 )
            self.f_old.Add (lfi_block_y)
            
            bfi_inner_x = BFI (name = "xmass", dim = 2,  
                            coef = [ConstantCF(1.0/self.dt),ConstantCF(1.0/self.dt)])
            bfi_block_x = CompoundBFI (bfi = bfi_inner_x, comp = 0 )
            self.a.Add (bfi_block_x)
            
            bfi_inner_y = BFI (name = "xmass", dim = 2,  
                           coef = [ConstantCF(1.0/self.dt),ConstantCF(1.0/self.dt)])
            bfi_block_y = CompoundBFI (bfi = bfi_inner_y, comp = 1 )
            self.a.Add (bfi_block_y)

    def Update(self, keep_old = False):
        self.velpre.fes.Update()
        # the order of the following operations is important as ....gf.Update() empties the vector if dimension has changed...
        if (self.initial == False): 
            self.f_old.Assemble()
        self.velpre.gf.Update()
        self.f.Assemble()
        self.a.Assemble(reallocate=True)

    def Solve(self,printrates = False):
        self.c.Update()
        solver = CGSolver (self.a.mat, self.c.mat, printrates=printrates)

        if (self.initial == False):
            self.f.vec.data = self.f.vec.data + 1.0/self.dt * self.f_old.vec.data
        if (False):
            self.velpre.gf.components[1].components[0].Set(coefficient = ConstantCF(-0.1), boundary = True)
            self.f.vec.data = self.f.vec.data - self.a.mat *  self.velpre.gf.vec.data
            tmp = self.velpre.gf.vec.CreateVector()
            tmp = self.velpre.gf.vec
            self.velpre.gf.vec.data = solver * self.f.vec.data
            self.velpre.gf.vec.data = self.velpre.gf.vec.data + tmp
        else:
            self.velpre.gf.vec.data = solver * self.f.vec.data
        
class npInstatStokes(PyNumProc):

    def Do(self, heap):
        
        print ("solve instationary stokes problem")
        
        matparams = material_params_water_butanol
        solverparams = solver_params_water_butanol_default

        pde = self.pde
        mesh = pde.Mesh()
        coef_initial_lset = pde.coefficients["initial_lset"]

        lset = Levelset(mesh = mesh, init_lset = coef_initial_lset, 
                        order = solverparams["lsetorder"])
        velpre = VelocityPressure(mesh, lset, dirichlet_vel=[1,2,3,4], 
                                  dirichlet_vel_vals = [ConstantCF(solverparams["relvelx"]),
                                                        ConstantCF(solverparams["relvely"])],
                                  ref_space=solverparams["ref_space"], 
                                  order=solverparams["velorder"]-1)

        lset_solver = LevelsetSolver(lset,velpre,dt=solverparams["dt"])

        if (solverparams["initial_cond"] == "stokes"):
            init_stokes_solver = StokesSolver(velpre,lset,dt=solverparams["dt"], initial = True)

            init_stokes_solver.Update()
            init_stokes_solver.Solve()

            print("after initial stokes solve")

        stokes_solver = StokesSolver(velpre,lset,params=matparams,dt=solverparams["dt"])

        print("before time loop - waiting for input(press enter) to start..")
        input()

        for i in range(1,solverparams["timesteps"]+1):
            lset_solver.Update()
            lset_solver.Solve()
            stokes_solver.Update()
            stokes_solver.Solve()

            Redraw(blocking=True)
        
            print ('\rtime step ' + repr(i) + ' / ' + repr(solverparams["timesteps"]) + ' done. (ndof: ' + repr(velpre.fes.ndof) +')', end='');

        print("simulation finished")
        input()


        
