{
  description = "mzgb — fast CLI for filtering very large log files";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system};
        in {
          default = pkgs.python3Packages.buildPythonApplication {
            pname = "mzgb";
            version = "0.3.0";
            src = self;
            format = "pyproject";
            nativeBuildInputs = [ pkgs.python3Packages.setuptools ];
            propagatedBuildInputs = with pkgs.python3Packages; [
              click
              rich
              python-dateutil
            ];
            meta = with pkgs.lib; {
              description = "Fast CLI for filtering very large log files";
              homepage = "https://github.com/mukesudo/mzgb";
              license = licenses.mit;
              mainProgram = "mzgb";
            };
          };
        });

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/mzgb";
        };
      });
    };
}
