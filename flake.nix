# To install:
#
# # flake.nix
# inputs = {
#   vdal.url = "github:ChristianWSmith/vdal";
# };
#
# # Reference the package like this:
# inputs.vdal.defaultPackage.x86_64-linux

{
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      {
        packages = 
          with import nixpkgs { inherit system; };
          (pkgs.callPackage ./default.nix {});
        defaultPackage = self.packages.${system};
      }
    );
}
