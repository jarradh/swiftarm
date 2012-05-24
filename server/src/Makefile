cppflags_for_gpp= -O2 -I . -I $(SWIFTARM)/server/include -I $(SWIFTARM)/server/lib/include
cppflags_for_x86_64= -O2 -I . -I $(SWIFTARM)/server/include -I $(SWIFTARM)/server/lib/include64
cppflags_for_arm= -O2 -I . -I $(SWIFTARM)/server/include -I $(SWIFTARM)/server/lib-arm/include -I /opt/armv7a8-toolchain-lite/arm-v7a8-linux-gnueabi/include -I /opt/armv7a8-toolchain-lite/arm-v7a8-linux-gnueabi/libc/include

ifeq ($(CXX),g++)
	ifeq ($(system),x86_64)
		CPPFLAGS=$(cppflags_for_x86_64)
		LDADD=$(SWIFTARM)/server/lib/libswift64.a $(SWIFTARM)/server/lib/lib64/libevent_pthreads.a $(SWIFTARM)/server/lib/lib64/libevent.a -lrt -lstdc++ -lgcc -lutil -lpthread
	else
		CPPFLAGS=$(cppflags_for_gpp)
		LDADD=$(SWIFTARM)/server/lib/libswift.a $(SWIFTARM)/server/lib/lib/libevent_pthreads.a $(SWIFTARM)/server/lib/lib/libevent.a -lrt -lstdc++ -lgcc -lutil -lpthread
	endif
else
	CPPFLAGS=$(cppflags_for_arm)
	LD=arm-v7a8-linux-gnueabi-ld
	LDADD=$(SWIFTARM)/server/lib-arm/libswift.a $(SWIFTARM)/server/lib-arm/lib/libevent_pthreads.a $(SWIFTARM)/server/lib-arm/lib/libevent.a -lrt -lstdc++ -lgcc -lutil -lpthread
endif

CPPFLAGS +=-Wall -Wno-sign-compare -Wno-unused -g -D_FILE_OFFSET_BITS=64 -D_LARGEFILE_SOURCE 

all: main

main: Main.o HttpServer.o Download.o DownloadManager.o
	$(CXX) ${CPPFLAGS} -o ws *.o ${LDADD}

Main.o: Main.cpp
	$(CXX) $(CPPFLAGS) Main.cpp -c

Download.o: Download.cpp
	$(CXX) $(CPPFLAGS) Download.cpp -c

DownloadManager.o: DownloadManager.cpp
	$(CXX) $(CPPFLAGS) DownloadManager.cpp -c

HttpServer.o: HttpServer.cpp
	$(CXX) $(CPPFLAGS) HttpServer.cpp -c

clean:
	rm -f *.o ws 2>/dev/null

.PHONY: clean all