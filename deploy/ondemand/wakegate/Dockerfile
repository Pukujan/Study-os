# wakegate: wake-on-request reverse proxy (stdlib Go, static binary, ~10 MB RAM).
FROM golang:1.25-alpine AS build
WORKDIR /src
COPY go.mod main.go ./
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /wakegate .

FROM scratch
COPY --from=build /wakegate /wakegate
EXPOSE 8000 8082
HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD ["/wakegate", "healthcheck"]
ENTRYPOINT ["/wakegate"]
