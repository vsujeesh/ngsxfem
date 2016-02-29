#pragma once

/// from ngsolve
#include <fem.hpp>   // for ScalarFiniteElement
#include <ngstd.hpp> // for Array
#include <comp.hpp>  // for Gridfunction, Coeff...
#include "calcpointshift.hpp"


namespace ngcomp
{

  void ProjectShift (shared_ptr<GridFunction> lset_ho, shared_ptr<GridFunction> lset_p1,
                     shared_ptr<GridFunction> deform, shared_ptr<CoefficientFunction> qn,
                     double lower_lset_bound, double upper_lset_bound, double threshold,
                     LocalHeap & lh);
    
  
  class NumProcProjectShift : public NumProc
  {
  protected:
    double lower_lset_bound;
    double upper_lset_bound;
    double threshold;
    shared_ptr<GridFunction> gf_lset_p1;
    shared_ptr<GridFunction> lset;
    shared_ptr<CoefficientFunction> qn;
    shared_ptr<GridFunction> deform;
    
  public:
    NumProcProjectShift (shared_ptr<PDE> apde, const Flags & flags);
    virtual ~NumProcProjectShift() { }

    virtual string GetClassName () const
    {
      return "NumProcProjectShift";
    }
    
    virtual void Do (LocalHeap & lh);
  };

}