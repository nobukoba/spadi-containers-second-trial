void compare() {
 TFile a(gSystem->Getenv("RARIS_OFFLINE")),b(gSystem->Getenv("RARIS_ONLINE")); bool ok=!a.IsZombie()&&!b.IsZombie();
 for(auto n:{"tf_count","hbf_count","hit_count"}) { auto x=(TParameter<Long64_t>*)a.Get(n);auto y=(TParameter<Long64_t>*)b.Get(n); if(!x||!y){ok=false;continue;} printf("%s offline=%lld online=%lld\n",n,x->GetVal(),y->GetVal());ok &= x->GetVal()==y->GetVal(); }
 for(auto n:{"channel","tdc","tot"}) {auto x=(TH1*)a.Get(n);auto y=(TH1*)b.Get(n);if(!x||!y||x->GetNbinsX()!=y->GetNbinsX()){ok=false;continue;} int diff=0;for(int i=0;i<=x->GetNbinsX()+1;i++)diff += x->GetBinContent(i)!=y->GetBinContent(i);printf("%s differing bins=%d\n",n,diff);ok &= diff==0;}
 for(auto f:{&a,&b}) {auto p=(TParameter<int>*)f->Get("failed");auto t=(TParameter<Long64_t>*)f->Get("tf_count");ok &= p && !p->GetVal() && t && t->GetVal()>0;} gSystem->Exit(ok?0:1);
}
