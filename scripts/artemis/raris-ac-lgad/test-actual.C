void test_actual() {
 TFile f(gSystem->Getenv("RARIS_OUTPUT"));bool ok=!f.IsZombie();
 for(auto p: {std::pair<const char*,Long64_t>{"tf_count",2815},{"hbf_count",33780},{"hit_count",68956}}) {auto v=(TParameter<Long64_t>*)f.Get(p.first);ok &= v && v->GetVal()==p.second;}
 for(auto n:{"channel","tdc","tot"}){auto h=(TH1*)f.Get(n);ok &= h && h->GetEntries()==68956;}
 auto bad=(TParameter<int>*)f.Get("failed");ok &= bad && !bad->GetVal();gSystem->Exit(ok?0:1);
}
