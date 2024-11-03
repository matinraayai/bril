#ifndef EMBED_MODIFIED_BITCODE_PASS_HPP
#define EMBED_MODIFIED_BITCODE_PASS_HPP
#include <llvm/IR/PassManager.h>

namespace llvm {
class Module;

/// \brief This pass intercepts the module at the end of the optimization
/// pipeline. It first clones the module, then removes the body of functions
/// annotated \c patch_point and marks them external. It also removes the
/// definition of all global variables and makes them external.
class EmbedModifiedBitcodePass
    : public llvm::PassInfoMixin<EmbedModifiedBitcodePass> {

public:
  EmbedModifiedBitcodePass() = default;

  PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &);

  static bool isRequired() { return true; }
};

} // namespace llvm

#endif