#include "TProcessor.h"
#include "TSegmentedData.h"
#include "TRawDataTimingCharge.h"
#include "TH1D.h"
#include "TFile.h"
class RarisHist : public art::TProcessor {
public:
 RarisHist() : seg(nullptr),h(nullptr),t(nullptr),q(nullptr) { RegisterProcessorParameter("OutputFile","output",out,TString("/tmp/raris-hist.root")); }
 void Init(art::TEventCollection* c) override { seg=(art::TSegmentedData**)c->GetObjectRef("segdata"); if(!seg){SetStateError("missing segdata");return;} h=new TH1D("channel","channel",128,0,128);t=new TH1D("tdc","tdc",512,0,536870912);q=new TH1D("tot","tot",512,0,4194304); }
 void Process() override { if(!seg || !*seg)return; for(auto obj:**seg) { auto a=dynamic_cast<TObjArray*>(obj); if(!a)continue; for(auto x:*a) {auto hit=dynamic_cast<art::TRawDataTimingCharge*>(x);if(!hit)continue;h->Fill(hit->GetCh());t->Fill(hit->GetTiming());q->Fill(hit->GetCharge());} } }
 void EndOfRun() override { TFile f(out,"RECREATE");h->Write();t->Write();q->Write();f.Close(); }
private:
 art::TSegmentedData **seg; TH1D *h,*t,*q; TString out;
 ClassDef(RarisHist,1)
};
