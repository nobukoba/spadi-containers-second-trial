#include <zmq.h>
#include <cstdio>
#include <cstdint>
int main(){void* c=zmq_ctx_new(); void*s=zmq_socket(c,ZMQ_PULL); int timeout=15000; zmq_setsockopt(s,ZMQ_RCVTIMEO,&timeout,sizeof(timeout)); zmq_connect(s,"tcp://127.0.0.1:5501"); FILE*f=fopen("/tmp/raris-capture.dat","wb"); if(!f)return 2; unsigned n=0; while(true){zmq_msg_t m;zmq_msg_init(&m); if(zmq_msg_recv(&m,s,0)<0){zmq_msg_close(&m);break;} uint32_t len=zmq_msg_size(&m); int more=zmq_msg_more(&m); fwrite(&len,4,1,f);fwrite(&more,4,1,f);fwrite(zmq_msg_data(&m),1,len,f);zmq_msg_close(&m); if(!more)n++;} fclose(f);zmq_close(s);zmq_ctx_destroy(c);printf("captured %u TFs\n",n);return 0;}
