import pytest
from ngsolve import *
from xfem import *
from netgen.geom2d import SplineGeometry
from math import pi

@pytest.mark.parametrize("quad_dominated", [True, False])
@pytest.mark.parametrize("order", [2,4,8])
@pytest.mark.parametrize("domain", [NEG, POS, IF])

def test_new_integrateX_via_circle_geom(quad_dominated, order, domain):
    square = SplineGeometry()
    square.AddRectangle([0,0],[1,1],bc=1)
    mesh = Mesh (square.GenerateMesh(maxh=100, quad_dominated=quad_dominated))
    r=0.6

    levelset = sqrt(x*x+y*y)-r
    referencevals = { POS : 1-pi*r*r/4, NEG : pi*r*r/4, IF : r*pi/2}

    n_ref = 8
    errors = []

    for i in range(n_ref):
        V = H1(mesh,order=1)
        lset_approx = GridFunction(V)
        InterpolateToP1(levelset,lset_approx)
    
        f = CoefficientFunction(1)
    
        integral = NewIntegrateX(lset=lset_approx,mesh=mesh,cf=f,order=order,domain_type=domain,heapsize=1000000)
        print("Result of Integration Reflevel ",i,", Key ",domain," : ", integral)
        errors.append(abs(integral - referencevals[domain]))

        if i < n_ref - 1:
            mesh.Refine()
        
    eoc = [log(errors[i+1]/errors[i])/log(0.5) for i in range(n_ref-1)]

    print("L2-errors:", errors)
    print("experimental order of convergence (L2):", eoc)

    mean_eoc_array = eoc[1:]
    mean_eoc = sum(mean_eoc_array)/len(mean_eoc_array)
    assert mean_eoc > 1.75

@pytest.mark.parametrize("quad_dominated", [True, False])
@pytest.mark.parametrize("order", [2,4,8])
@pytest.mark.parametrize("domain", [NEG, POS, IF])

def test_new_integrateX_via_straight_cutted_quad2D(order, domain, quad_dominated):
    square = SplineGeometry()
    square.AddRectangle([0,0],[1,1],bc=1)
    mesh = Mesh (square.GenerateMesh(maxh=100, quad_dominated=quad_dominated))
    
    levelset = 1 - 2*x - 2*y
    
    domains = [NEG,POS,IF]
    referencevals = {NEG: 7/8, POS: 1/8, IF: 1/sqrt(2)}
    
    lset_approx = GridFunction(H1(mesh,order=1))
    InterpolateToP1(levelset,lset_approx)
    
    f = CoefficientFunction(1)
    
    integral = NewIntegrateX(lset=lset_approx,mesh=mesh,cf=f,order=order,domain_type=domain,heapsize=1000000)
    error = abs(integral - referencevals[domain])
    
    assert error < 5e-16*(order+1)*(order+1)
