void verify() {
  const char *path=gSystem->Getenv("RARIS_OUTPUT"); TFile f(path,"READ");
  auto failed=(TParameter<int>*)f.Get("failed"); auto tfs=(TParameter<Long64_t>*)f.Get("tf_count");
  if(f.IsZombie() || !failed || !tfs || failed->GetVal() || tfs->GetVal()<=0) { Error("verify","analysis failed or received no TFs");gSystem->Exit(1); }
  printf("TFs: %lld\n",tfs->GetVal());
}
