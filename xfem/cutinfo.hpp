#pragma once

/// from ngsolve
#include <solve.hpp>
#include <comp.hpp>
#include <fem.hpp>

/// from ngxfem
#include "../cutint/xintegration.hpp"
// #include "../xfem/xfiniteelement.hpp"

using namespace ngsolve;
using namespace xintegration;
// using namespace cutinfo;

namespace ngcomp
{

  template <int D> class T_XFESpace; // forward declaration

  class CutInformation
  {
    template <int D> friend class T_XFESpace;
  protected:
    shared_ptr<MeshAccess> ma;
    shared_ptr<VVector<double>> cut_ratio_of_element [2] = {nullptr, nullptr};
    shared_ptr<BitArray> elems_of_domain_type [3] = {nullptr, nullptr, nullptr};
    shared_ptr<BitArray> selems_of_domain_type [3] = {nullptr, nullptr, nullptr};
    shared_ptr<BitArray> facets_of_domain_type [3] = {nullptr, nullptr, nullptr};
    shared_ptr<BitArray> cut_neighboring_node [6] = {nullptr, nullptr, nullptr,
                                                     nullptr, nullptr, nullptr};
    shared_ptr<Array<DOMAIN_TYPE>> dom_of_node [6] = {nullptr, nullptr, nullptr,
                                                      nullptr, nullptr, nullptr};
    double subdivlvl = 0;
  public:
    CutInformation (shared_ptr<MeshAccess> ama);
    void Update(shared_ptr<CoefficientFunction> lset, LocalHeap & lh);

    shared_ptr<MeshAccess> GetMesh () const { return ma; }

    shared_ptr<BaseVector> GetCutRatios (VorB vb) const
    {
      return cut_ratio_of_element[vb];
    }

    INLINE DOMAIN_TYPE DomainTypeOfElement(ElementId elid)
    {
      int elnr = elid.Nr();
      VorB vb = elid.VB();
      shared_ptr<BitArray> * ba = nullptr;
      if (vb == VOL)
        ba = elems_of_domain_type;
      else
        ba = selems_of_domain_type;

      if (ba[IF]->Test(elnr))
        return IF;
      else
      {
        if (ba[NEG]->Test(elnr))
          return NEG;
        else
          return POS;
      }
    }

    // template <NODE_TYPE NT>
    // DOMAIN_TYPE GetDomainOfNode (int nr)
    // {
    //   if (GetCutRatioOfNode<NT>(nr) > 0.0 && GetCutRatioOfNode<NT>(nr) < 1.0)
    //     return IF;
    //   else
    //     return GetCutRatioOfNode<NT>(nr) == 0.0 ? NEG : POS;
    // }

    shared_ptr<BitArray> GetElementsOfDomainType(DOMAIN_TYPE dt, VorB vb) const
    {
      if (vb == VOL)
        return elems_of_domain_type[dt];
      else
        return selems_of_domain_type[dt];
    }

    shared_ptr<BitArray> GetFacetsOfDomainType(DOMAIN_TYPE dt) const { return facets_of_domain_type[dt]; }

  };

  shared_ptr<BitArray> GetFacetsWithNeighborTypes(shared_ptr<MeshAccess> ma,
                                                  shared_ptr<BitArray> a,
                                                  shared_ptr<BitArray> b,
                                                  bool bound_val_a,
                                                  bool bound_val_b,
                                                  bool ask_and,
                                                  LocalHeap & lh);
  shared_ptr<BitArray> GetElementsWithNeighborFacets(shared_ptr<MeshAccess> ma,
                                                     shared_ptr<BitArray> a,
                                                     LocalHeap & lh);

  shared_ptr<BitArray> GetDofsOfElements(shared_ptr<FESpace> fes,
                                         shared_ptr<BitArray> a,
                                         LocalHeap & lh);


}