{
  description = "A simple Python development environment inside an FHS sandbox";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";
  };

  outputs = { self, nixpkgs, systems, unstable }:
    let
      eachSystem = nixpkgs.lib.genAttrs (import systems);
    in {
      devShells = eachSystem (system:
        let
          # System x86_64, ARM64, ...
          pkgs = nixpkgs.legacyPackages.${system};
          unstable-pkgs = unstable.legacyPackages.${system};

          fhs = pkgs.buildFHSEnv {
            name = "python-fhs";

            targetPkgs = _: [
              # Python
              (unstable-pkgs.python313.withPackages (ps: [
                ps.virtualenv
                ps.uv
                ps.pip
              ]))
              
              # Dependencies
              pkgs.opus-tools
              pkgs.ffmpeg

              # Env
              pkgs.direnv # `.envrc` or `.dotenvrc` files
            ];

            runScript = "zsh";

            # Shell init
            profile = ''
              if [ '.env' ]; then source .env; fi
              direnv allow

              echo "Python FHS environment active."

              python --version
            '';
          };
        in {
          default = fhs.env;
        }
      );
    };
}
