{ pkgs ? import <nixpkgs> {}
, shell ? false
, vdal-version ? "0.0.1"
}:

with pkgs;
with pkgs.lib;

stdenv.mkDerivation rec {

  name = "vdal";

  buildInputs = [
    python311
  ]
  ++ optionals shell (
    [ # Development shell dependencies
    ]
  );

  src = if shell then null else ./src;

  installPhase = ''
    mkdir -p $out/bin
    cp $src/main.py $out/bin/vdal
    chmod +x $out/bin/vdal
  '';

  meta = {
    description = "Very Dumb Application Launcher";
    license = licenses.mit;
  };
}
