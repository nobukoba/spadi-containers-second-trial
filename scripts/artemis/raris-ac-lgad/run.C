#include "TLoopManager.h"
void run() {
  const char* source = gSystem->Getenv("RARIS_SOURCE");
  const char* steering = gSystem->Getenv("RARIS_STEERING");
  if (!source || !steering || gSystem->Load("libzmq") < 0 || !gSystem->CompileMacro(source,"k")) { gSystem->Exit(1); return; }
  auto loop = art::TLoopManager::Instance()->Add(steering);
  if (!loop) { gSystem->Exit(1); return; }
  loop->Resume(); loop->Terminate();
}
