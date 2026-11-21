#include "TLoopManager.h"
void run() {
  const char* library = gSystem->Getenv("RARIS_LIBRARY");
  const char* steering = gSystem->Getenv("RARIS_STEERING");
  if (!library || !steering || gSystem->Load("libzmq") < 0 || gSystem->Load(library) < 0) { gSystem->Exit(1); return; }
  auto loop = art::TLoopManager::Instance()->Add(steering);
  if (!loop) { gSystem->Exit(1); return; }
  loop->Resume(); loop->Terminate();
}
