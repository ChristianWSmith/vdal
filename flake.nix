{
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      {
        packages = with import nixpkgs { inherit system; };
        package = (pkgs.callPackage ./default.nix {});
        # vdal.override { version = ./.; };
        defaultPackage = self.packages.${system};
      }
    );
}
