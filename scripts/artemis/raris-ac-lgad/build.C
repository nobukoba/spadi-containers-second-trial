// Run only while constructing the FULL image, where the ARTEMIS build toolchain exists.
void build() {
  if (gSystem->Load("libzmq") < 0 || !gSystem->CompileMacro("RarisProcessor.C", "k")) {
    Error("build", "cannot build the RARiS processor");
    gSystem->Exit(1);
  }
}
