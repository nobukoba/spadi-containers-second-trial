#include "TProcessor.h"
#include "TFile.h"
#include "TH1D.h"
#include "TParameter.h"
#include <zmq.h>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

// Issue #7 prototype: one ARTEMIS event is one TF, with four HBFs per source.
class RarisProcessor : public art::TProcessor {
 public:
  RarisProcessor() {
    RegisterProcessorParameter("InputFiles", "Three FileSink STF files", files, art::StringVec_t());
    RegisterProcessorParameter("Endpoint", "ZeroMQ PULL endpoint; empty for files", endpoint, TString(""));
    RegisterProcessorParameter("OutputFile", "ROOT histogram file", output, TString("raris.root"));
    RegisterProcessorParameter("TimeoutMs", "Online receive timeout in milliseconds", timeout, 30000);
  }
  ~RarisProcessor() override { if (socket) zmq_close(socket); if (context) zmq_ctx_term(context); }
  void Init(art::TEventCollection*) override {
    try {
      if (endpoint.Length()) {
        context = zmq_ctx_new(); socket = zmq_socket(context, ZMQ_PULL);
        if (!context || !socket || zmq_setsockopt(socket,ZMQ_RCVTIMEO,&timeout,sizeof(timeout)) || zmq_connect(socket,endpoint.Data())) throw std::runtime_error("cannot connect PULL socket");
      } else {
        if (files.size()!=3) throw std::runtime_error("three input files required");
        for (auto &path: files) {
          inputs.emplace_back(path.Data(), std::ios::binary);
          auto &f=inputs.back(); char hdr[304]; f.read(hdr,304);
          if (!f || std::memcmp(hdr,"FILESNK\0",8) || u16(hdr+12)!=304) throw std::runtime_error("invalid FileSink header");
        }
      }
      channel = new TH1D("channel","Channel;channel;hits",256,0,256);
      tdc = new TH1D("tdc","TDC;raw TDC;hits",512,0,536870912.0);
      tot = new TH1D("tot","Time over threshold;raw TOT;hits",512,0,4194304.0);
      channel->SetDirectory(nullptr); tdc->SetDirectory(nullptr); tot->SetDirectory(nullptr);
    } catch (const std::exception &e) { Error("Init", "%s", e.what()); SetStateError("RARiS initialization failed"); }
  }
  void Process() override {
    try {
      std::vector<std::vector<char>> stfs;
      if (socket) {
        std::vector<std::vector<char>> parts;
        while (true) {
          zmq_msg_t msg; zmq_msg_init(&msg); int n=zmq_msg_recv(&msg,socket,0);
          if(n<0) { zmq_msg_close(&msg); if(parts.empty()) { if(tfs==0) { Error("Process", "no TF received before timeout"); failed=true; } stop(); return; } throw std::runtime_error("truncated multipart TF"); }
          bool more=zmq_msg_more(&msg); auto *p=(char*)zmq_msg_data(&msg); parts.emplace_back(p,p+n); zmq_msg_close(&msg); if(!more) break;
        }
        if(parts.empty() || parts[0].size()!=24 || std::memcmp(parts[0].data(),"TIMEFRM\0",8)) throw std::runtime_error("invalid TF header");
        uint32_t id=u32(parts[0].data()+16), count=u32(parts[0].data()+20);
        for(size_t i=1;i<parts.size();++i) {
          auto &p=parts[i];
          if(p.size()==48 && !std::memcmp(p.data(),"SUBTIME\0",8)) { if(u32(p.data()+16)!=id) throw std::runtime_error("TF/STF id mismatch"); stfs.push_back(p); }
          else { if(stfs.empty()) throw std::runtime_error("payload before STF"); stfs.back().insert(stfs.back().end(),p.begin(),p.end()); }
        }
        if(stfs.size()!=count) throw std::runtime_error("TF source count mismatch");
      } else {
        for(auto &f:inputs) {
          char hdr[48]; f.read(hdr,48);
          if(f.gcount()==48 && !std::memcmp(hdr,"FILETRL\0",8)) { stop(); return; }
          if(f.gcount()!=48 || std::memcmp(hdr,"SUBTIME\0",8)) throw std::runtime_error("invalid STF header");
          uint32_t size=u32(hdr+8); if(u16(hdr+12)!=48 || size<48 || size>16*1024*1024) throw std::runtime_error("invalid STF size");
          stfs.emplace_back(hdr,hdr+48); auto &s=stfs.back(); s.resize(size); f.read(s.data()+48,size-48); if(!f) throw std::runtime_error("truncated STF");
        }
        if(u32(stfs[0].data()+16)!=u32(stfs[1].data()+16) || u32(stfs[0].data()+16)!=u32(stfs[2].data()+16)) throw std::runtime_error("offline sources have different STF IDs");
      }
      for(auto &s:stfs) decode(s); ++tfs;
    } catch(const std::exception &e) { Error("Process", "%s",e.what()); failed=true; stop(); }
  }
  void EndOfRun() override {
    TFile f(output,"RECREATE"); channel->Write();tdc->Write();tot->Write();
    TParameter<Long64_t>("tf_count",tfs).Write();TParameter<Long64_t>("hbf_count",hbfs).Write();TParameter<Long64_t>("hit_count",hits).Write();TParameter<int>("failed",failed).Write();f.Close();
  }
 private:
  static uint16_t u16(const char*p){return uint16_t((unsigned char)p[0]) | uint16_t((unsigned char)p[1])<<8;}
  static uint32_t u32(const char*p){return uint32_t(u16(p)) | uint32_t(u16(p+2))<<16;}
  static uint64_t u64(const char*p){return uint64_t(u32(p)) | uint64_t(u32(p+4))<<32;}
  void stop(){SetStopEvent();SetStopLoop();SetEndOfRun();}
  void decode(const std::vector<char>&s) {
    if(s.size()<48 || u32(s.data()+8)!=s.size()) throw std::runtime_error("STF length mismatch");
    auto type=u32(s.data()+20); if(type!=5 && type!=6) throw std::runtime_error("unsupported FEM type");
    for(size_t p=48;p<s.size();) {
      if(p+16>s.size() || std::memcmp(s.data()+p,"HRTBEAT\0",8)) throw std::runtime_error("invalid HBF header");
      auto n=u32(s.data()+p+8); if(u16(s.data()+p+12)!=16 || n<32 || n%8 || p+n>s.size()) throw std::runtime_error("invalid HBF size");
      if((u64(s.data()+p+n-16)>>58)!=28 || (u64(s.data()+p+n-8)>>58)!=30) throw std::runtime_error("invalid heartbeat pair");
      for(size_t k=p+16;k<p+n-16;k+=8){auto w=u64(s.data()+k); if((w>>58)!=11)continue; auto ch=type==5?((w>>51)&127):((w>>50)&255);auto tim=type==5?(w&0x1fffffff):((w>>15)&0x7ffff);auto charge=type==5?((w>>29)&0x3fffff):((w>>34)&0xffff);channel->Fill(ch);tdc->Fill(tim);tot->Fill(charge);++hits;}
      ++hbfs;p+=n;
    }
  }
  art::StringVec_t files; TString endpoint,output; int timeout; std::vector<std::ifstream> inputs; //!
  void *context=nullptr,*socket=nullptr; TH1D *channel=nullptr,*tdc=nullptr,*tot=nullptr;
  Long64_t tfs=0,hbfs=0,hits=0; bool failed=false;
  ClassDef(RarisProcessor,1)
};
