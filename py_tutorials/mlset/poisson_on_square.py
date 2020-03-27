# ------------------------------ LOAD LIBRARIES -------------------------------
from netgen.geom2d import SplineGeometry
from ngsolve import *
from ngsolve.solvers import PreconditionedRichardson as PreRic
from xfem import *
from xfem.mlset import *

ngsglobals.msg_level = 2
SetNumThreads(4)


# -------------------------------- PARAMETERS ---------------------------------
h0 = 0.4
Lx = 3
k = 1

gamma_n = 10
gamma_s = 0.1

inverse = "pardiso"


# ----------------------------------- DATA ------------------------------------
u_ex = 16 * x * (1 - x) * y * (1 - y)
grad_u_ex = CoefficientFunction((16 * (1 - 2 * x) * y * (1 - y), 
                                 16 * x * (1 - x) * (1 - 2 * y)))
rhs = 32 * (y * (1 - y) + x * (1 - x))


def level_sets():
    return [-y, x - 1, y - 1, -x]


nr_ls = len(level_sets())


# ------------------------------ BACKGROUND MESH ------------------------------
geo = SplineGeometry()
geo.AddRectangle((-0.2, -0.2), (1.2, 1.2),
                 bcs=("bottom", "right", "top", "left"))
ngmesh = geo.GenerateMesh(maxh=h0)
for i in range(Lx):
    ngmesh.Refine()
mesh = Mesh(ngmesh)


# --------------------------- FINITE ELEMENT SPACE ----------------------------
V = H1(mesh, order=k, dgjumps=True)

gfu = GridFunction(V)
freedofs = BitArray(V.ndof)


# ---------------------------- LEVELSET & CUT-INFO ----------------------------
level_sets_p1 = tuple(GridFunction(H1(mesh, order=1)) for i in range(nr_ls))
for i, lsetp1 in enumerate(level_sets_p1):
    InterpolateToP1(level_sets()[i], lsetp1)
    Draw(lsetp1, mesh, "lsetp1_{}".format(i))

square = DomainTypeArray([(NEG, NEG, NEG, NEG)])

lset_dom_inner = {"levelset": level_sets_p1, "domain_type": square.dtlist}
lsets_bnd = []
for i in range(nr_ls):
    dtt = tuple(IF if ii == i else NEG for ii in range(nr_ls))
    lsets_bnd.append({"levelset": level_sets_p1, "domain_type": dtt})

mlci = MultiLevelsetCutInfo(mesh, level_sets_p1)


# ------------------------------ ELEMENT MARKERS ------------------------------
els_hasneg, els_if = BitArray(mesh.ne), BitArray(mesh.ne)
els_if_singe = [BitArray(mesh.ne) for i in range(nr_ls)]
facets_gp = BitArray(mesh.nedge)

els_hasneg[:] = False
els_hasneg |= mlci.GetElementsWithContribution(square.dtlist)

els_if[:] = False
els_if |= els_hasneg & ~mlci.GetElementsOfType(square.dtlist)
Draw(BitArrayCF(els_if), mesh, "els_if")

for i in range(nr_ls):
    els_if_singe[i][:] = False
    els_if_singe[i] |= els_hasneg
    els_if_singe[i] &= mlci.GetElementsWithContribution(lsets_bnd[i]["domain_type"])
    Draw(BitArrayCF(els_if_singe[i]),mesh,"els_if_singe"+str(i))

facets_gp[:] = False
facets_gp |= GetFacetsWithNeighborTypes(mesh, a=els_hasneg, b=els_if,
                                        use_and=True)

els_gp = GetElementsWithNeighborFacets(mesh, facets_gp)
Draw(BitArrayCF(els_gp), mesh, "gp_elements")

freedofs[:] = False
freedofs |= GetDofsOfElements(V, els_hasneg) & V.FreeDofs()


# ----------------------------- (BI)LINEAR FORMS ------------------------------
u, v = V.TnT()
h = specialcf.mesh_size
n_lsets = [1.0 / Norm(grad(lsetp1)) * grad(lsetp1) for lsetp1 in level_sets_p1]

diffusion = InnerProduct(Grad(u), Grad(v))

nitsche_terms = [- InnerProduct(Grad(u) * n, v)
                 - InnerProduct(Grad(v) * n, u)
                 + (gamma_n * k * k / h) * InnerProduct(u, v) for n in n_lsets]

ghost_penalty = gamma_s / (h**2) * (u - u.Other()) * (v - v.Other())

forcing = rhs * v


# -------------------------------- INTEGRATORS --------------------------------
a = RestrictedBilinearForm(V, element_restriction=els_hasneg,
                           facet_restriction=facets_gp, check_unused=False)
a += SymbolicBFI(lset_dom_inner, form=diffusion, definedonelements=els_hasneg)
for i, nitsche in enumerate(nitsche_terms):
    a += SymbolicBFI(lsets_bnd[i], form=nitsche,
                     definedonelements=els_if_singe[i])
a += SymbolicFacetPatchBFI(form=ghost_penalty, skeleton=False,
                           definedonelements=facets_gp)


f = LinearForm(V)
f += SymbolicLFI(lset_dom_inner, form=forcing)


# ------------------------------- SOLVE PROBLEM -------------------------------
with TaskManager():
    f.Assemble()
    a.Assemble()
    inv = a.mat.Inverse(freedofs=freedofs)

    gfu.vec.data = PreRic(a=a, rhs=f.vec, pre=inv, freedofs=freedofs)

# ------------------------------- VISUALISATION -------------------------------
Draw(gfu, mesh, "solution")
Draw((gfu - u_ex), mesh, "err")

# ------------------------------ POST-PROCESSING ------------------------------

with TaskManager():
    err_l2 = sqrt(Integrate(lset_dom_inner, cf=InnerProduct(gfu - u_ex, 
                                                            gfu - u_ex),
                            mesh=mesh, order=2 * k))
    err_h1 = sqrt(Integrate(lset_dom_inner, 
                            cf=InnerProduct(Grad(gfu) - grad_u_ex,
                                            Grad(gfu) - grad_u_ex),
                            mesh=mesh, order=2 * (k - 1)))

print("\n")
print("L2 error = {:1.3e}".format(err_l2))
print("H1 error = {:1.3e}".format(err_h1))