from firedrake import *


def test_nonlinear_variational_solver():
    from pyop2.gpu.cuda import cuda_backend as cuda
    mesh = UnitSquareMesh(32, 32)
    V = FunctionSpace(mesh, "CG", 1)
    u = TrialFunction(V)
    v = TestFunction(V)
    x, y = SpatialCoordinate(mesh)

    a = (dot(grad(v), grad(u)) + v * u) * dx
    f = Function(V)
    f.interpolate((1+8*pi*pi)*cos(x*pi*2)*cos(y*pi*2))
    L = f * v * dx
    u_gpu = Function(V)
    u_cpu = Function(V)
    sp = {"mat_type": "matfree",
          "ksp_monitor_true_residual": None,
          "ksp_converged_reason": None}
    with offloading(cuda):
        solve(a == L, u_gpu, solver_parameters=sp)

    solve(a == L, u_cpu, solver_parameters=sp)

    assert (sqrt(assemble(dot(u_cpu - u_gpu, u_cpu - u_gpu) *
        dx))/sqrt(assemble(dot(u_cpu, u_cpu) * dx))) < 1e-6

    with offloading(cuda):
        assert (sqrt(assemble(dot(u_cpu - u_gpu, u_cpu - u_gpu) *
            dx))/sqrt(assemble(dot(u_cpu, u_cpu) * dx))) < 1e-6


def test_linear_variational_solver():
    from pyop2.gpu.cuda import cuda_backend as cuda

    mesh = UnitSquareMesh(32, 32)
    V = FunctionSpace(mesh, "CG", 1)
    u = TrialFunction(V)
    v = TestFunction(V)
    f = Function(V)
    x, y = SpatialCoordinate(mesh)
    f.interpolate((1+8*pi*pi)*cos(x*pi*2)*cos(y*pi*2))

    L = assemble(f * v * dx)
    fem_soln = Function(V)

    with offloading(cuda):
        a = assemble((dot(grad(v), grad(u)) + v * u) * dx, mat_type='matfree')
        solve(a, fem_soln, L)

    f.interpolate(cos(x*pi*2)*cos(y*pi*2))
    print(sqrt(assemble(dot(fem_soln - f, fem_soln - f) * dx)))