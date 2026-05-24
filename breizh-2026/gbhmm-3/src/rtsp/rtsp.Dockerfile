FROM alpine:3.19

ARG MEDIAMTX_VERSION=1.9.0

RUN apk add --no-cache ffmpeg wget ca-certificates nginx

RUN ARCH=$(uname -m) && \
    case "$ARCH" in \
    x86_64)  MTX_ARCH=amd64 ;; \
    aarch64) MTX_ARCH=arm64v8 ;; \
    armv7l)  MTX_ARCH=armv7 ;; \
    *) echo "Unsupported arch: $ARCH" && exit 1 ;; \
    esac && \
    wget -q "https://github.com/bluenviron/mediamtx/releases/download/v${MEDIAMTX_VERSION}/mediamtx_v${MEDIAMTX_VERSION}_linux_${MTX_ARCH}.tar.gz" -O /tmp/mediamtx.tar.gz && \
    tar -xzf /tmp/mediamtx.tar.gz -C /usr/local/bin/ mediamtx && \
    rm /tmp/mediamtx.tar.gz

COPY video.mp4       /video.mp4
COPY mediamtx.yml    /mediamtx.yml
COPY nginx.conf      /etc/nginx/http.d/default.conf
COPY index.html      /usr/share/nginx/html/index.html
COPY pki/            /etc/tls/

EXPOSE 443
EXPOSE 8554

# nginx runs in the background; mediamtx is PID 1 and spawns the ffmpeg
# publisher via its runOnInit hook (see mediamtx.yml).
CMD ["sh", "-c", "nginx && exec mediamtx /mediamtx.yml"]
