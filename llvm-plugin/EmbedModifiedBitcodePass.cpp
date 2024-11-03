#include "EmbedModifiedBitcodePass.hpp"

#include "llvm/Passes/PassPlugin.h"
#include <llvm/ADT/StringExtras.h>
#include <llvm/Analysis/ValueTracking.h>
#include <llvm/Bitcode/BitcodeWriterPass.h>
#include <llvm/Demangle/Demangle.h>
#include <llvm/IR/Module.h>
#include <llvm/Passes/PassBuilder.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/Transforms/Utils/Cloning.h>
#include <llvm/Transforms/Utils/ModuleUtils.h>

namespace llvm {

static constexpr const char *PatchPointAnnotation = "patch_point";

/// Finds the set of annotated functions in \p M annotated as patch points.
/// \param [in] M Module to inspect
/// \param [out] PatchPoints a list of patch point functions found in \p M
/// \return any \c llvm::Error encountered during the process
static Error
getAnnotatedValues(const Module &M,
                   SmallVectorImpl<llvm::Function *> &PatchPoints) {
  const GlobalVariable *V = M.getGlobalVariable("llvm.global.annotations");
  if (V == nullptr)
    return Error::success();
  const llvm::ConstantArray *CA = cast<ConstantArray>(V->getOperand(0));
  for (Value *Op : CA->operands()) {
    auto *CS = cast<ConstantStruct>(Op);
    // The first field of the struct contains a pointer to the annotated
    // variable.
    Value *AnnotatedVal = CS->getOperand(0)->stripPointerCasts();
    if (auto *Func = dyn_cast<Function>(AnnotatedVal)) {
      // The second field contains a pointer to a global annotation string.
      auto *GV = cast<GlobalVariable>(CS->getOperand(1)->stripPointerCasts());
      StringRef Content;
      getConstantStringInfo(GV, Content);
      if (Content == PatchPointAnnotation) {
        PatchPoints.push_back(Func);
        outs() << "Found patch point " << Func->getName() << ".\n";
      }
    }
  }
  return Error::success();
}

PreservedAnalyses EmbedModifiedBitcodePass::run(Module &M,
                                                ModuleAnalysisManager &AM) {
  if (M.getGlobalVariable("llvm.embedded.module", /*AllowInternal=*/true))
    report_fatal_error(
        "Attempted to embed bitcode twice. Are you passing -fembed-bitcode?",
        /*gen_crash_diag=*/false);

  // Clone the module in order to preprocess it + not interfere with normal
  // compilation process
  auto ClonedModule = CloneModule(M);

  outs() << "Cloned module " << ClonedModule->getName()
         << " before modification:\n";
  ClonedModule->print(outs(), nullptr);

  // Extract all the patch points
  SmallVector<Function *, 4> PatchPoints;
  if (auto Err = getAnnotatedValues(*ClonedModule, PatchPoints))
    report_fatal_error(std::move(Err), true);

  // Remove the annotations variable from the Module now that it is processed
  auto AnnotationGV =
      ClonedModule->getGlobalVariable("llvm.global.annotations");
  if (AnnotationGV) {
    AnnotationGV->dropAllReferences();
    AnnotationGV->eraseFromParent();
  }

  // Remove the llvm.used and llvm.compiler.use variable list
  for (const auto &VarName : {"llvm.compiler.used", "llvm.used"}) {
    auto LLVMUsedVar = ClonedModule->getGlobalVariable(VarName);
    if (LLVMUsedVar != nullptr) {
      LLVMUsedVar->dropAllReferences();
      LLVMUsedVar->eraseFromParent();
    }
  }

  // Remove the body of each patch point function, and add a "patch_point"
  // attribute to them
  for (auto PatchPoint : PatchPoints) {
    PatchPoint->deleteBody();
    PatchPoint->setComdat(nullptr);
    PatchPoint->setCallingConv(llvm::CallingConv::AnyReg);
    PatchPoint->addFnAttr(PatchPointAnnotation);
    PatchPoint->removeFnAttr(Attribute::OptimizeNone);
  }

  // Convert all global variables to extern
  for (auto &GV : ClonedModule->globals()) {
    GV.setInitializer(nullptr);
    GV.setLinkage(GlobalValue::ExternalLinkage);
    GV.setVisibility(GlobalValue::DefaultVisibility);
    GV.setDSOLocal(false);
  }

  outs() << "Embedded Module " << ClonedModule->getName() << " dump: ";
  ClonedModule->print(outs(), nullptr);

  SmallVector<char> Data;
  raw_svector_ostream OS(Data);
  auto PA = BitcodeWriterPass(OS).run(*ClonedModule, AM);

  embedBufferInModule(M, MemoryBufferRef(toStringRef(Data), "ModuleData"),
                      ".llvmbc");

  return PA;
}

} // namespace llvm

llvm::PassPluginLibraryInfo getEmbedModifiedBitcodePassPluginInfo() {
  const auto Callback = [](llvm::PassBuilder &PB) {
    PB.registerOptimizerLastEPCallback(
        [](llvm::ModulePassManager &MPM, llvm::OptimizationLevel Opt) {
          MPM.addPass(llvm::EmbedModifiedBitcodePass());
        });
  };

  return {LLVM_PLUGIN_API_VERSION, "embed-modified-bitcode-pass",
          LLVM_VERSION_STRING, Callback};
}

#ifndef LLVM_LUTHIER_TOOL_COMPILE_PLUGIN_LINK_INTO_TOOLS
extern "C" LLVM_ATTRIBUTE_WEAK::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
  return getEmbedModifiedBitcodePassPluginInfo();
}
#endif