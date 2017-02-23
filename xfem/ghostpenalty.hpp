#ifndef FILE_GHOSTPENALTY_HPP
#define FILE_GHOSTPENALTY_HPP

#include <fem.hpp>   // for ScalarFiniteElement
#include <ngstd.hpp> // for Array

#include "../cutint/xintegration.hpp"
#include "xfiniteelement.hpp"
// #include "../spacetime/spacetimefe.hpp"
// #include "../spacetime/spacetimeintegrators.hpp"
// #include "../utils/stcoeff.hpp"

namespace ngfem
{


  template <int D, int difforder>
  class GhostPenaltyIntegrator : public FacetBilinearFormIntegrator
  {
  protected:
    shared_ptr<CoefficientFunction> coef_lam_neg;
    shared_ptr<CoefficientFunction> coef_lam_pos;
    double told = 0.0;
    double tnew = 1.0;
    double tau = 1.0;
    shared_ptr<CoefficientFunction> coef_delta;
  public:
    GhostPenaltyIntegrator (const Array<shared_ptr<CoefficientFunction>> & coeffs) 
      : FacetBilinearFormIntegrator()
    { 
      coef_lam_neg  = coeffs[0];
      coef_lam_pos  = coeffs[1];
      if (coeffs.Size()>3)
      {
        told = coeffs[2]->EvaluateConst();
        tnew = coeffs[3]->EvaluateConst();
        tau = tnew-told;
        coef_delta = coeffs[4];
      }
      else
        coef_delta = coeffs[2];
    }

    virtual ~GhostPenaltyIntegrator () { ; }
    
    virtual VorB VB () const { return VOL; }

    virtual bool IsSymmetric () const 
    { return true; }
    
    static Integrator * Create (const Array<shared_ptr<CoefficientFunction>> & coeffs)
    {
      return new GhostPenaltyIntegrator (coeffs);
    }

    virtual void SetTimeInterval (const TimeInterval & ti)
    { told = ti.first; tnew = ti.second; tau = tnew-told; }

    virtual void CalcElementMatrix (const FiniteElement & fel,
                                    const ElementTransformation & eltrans, 
                                    FlatMatrix<double> elmat,
                                    LocalHeap & lh) const
    {
      throw Exception("GhostPenaltyIntegrator::CalcElementMatrix - not implemented!");
    }
    
    virtual void CalcFacetMatrix (const FiniteElement & volumefel1, int LocalFacetNr1,
                                  const ElementTransformation & eltrans1, FlatArray<int> & ElVertices1,
                                  const FiniteElement & volumefel2, int LocalFacetNr2,
                                  const ElementTransformation & eltrans2, FlatArray<int> & ElVertices2,
                                  FlatMatrix<double> & elmat,
                                  LocalHeap & lh// ,
                                  // BitArray* twice
                                 ) const;

  };


  template <int D, int ORDER>
  class DiffOpDuDnk : public DiffOp<DiffOpDuDnk<D,ORDER> >
  {

  public:
    enum { DIM = 1 };          // just one copy of the spaces
    enum { DIM_SPACE = D };    // D-dim space
    enum { DIM_ELEMENT = D };  // D-dim elements (in contrast to boundary elements)
    enum { DIM_DMAT = 1 };     // D-matrix
    enum { DIFFORDER = ORDER };    // minimal differential order (to determine integration order)

    template <typename FEL, typename MIP, typename MAT>
    static void GenerateMatrix (const FEL & bfel, const MIP & sip,
                                MAT & mat, LocalHeap & lh);
  };


#ifndef FILE_GHOSTPENALTY_CPP
  extern template class T_DifferentialOperator<DiffOpDuDnk<2,1>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<2,2>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<2,3>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<2,4>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<2,5>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<2,6>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<2,7>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<2,8>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<3,1>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<3,2>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<3,3>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<3,4>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<3,5>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<3,6>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<3,7>>;
  extern template class T_DifferentialOperator<DiffOpDuDnk<3,8>>;
#endif

}

#endif
