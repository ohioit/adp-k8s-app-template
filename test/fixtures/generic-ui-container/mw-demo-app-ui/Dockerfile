# TODO: Customize this docker image to your needs, it will not
# work by default.

FROM debian-slim:latest # Change this to your desired base image

# Install dependencies or remove this RUN line
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get -y dist-upgrade \
    && apt-get install -y --no-install-recommends \
        # Add your dependencies here
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy your application files
COPY source dest

# Set the default port
EXPOSE 8000

# Set the default user
USER 1000:1000

# Set the default working directory
WORKDIR /app

# Set the default command
ENTRYPOINT [ "executable" ]
