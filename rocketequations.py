# rocketequations - a collection of rocket equation functions
# Tom Fetter @2015
# version 1.1


from math import *


g = 32    # acceleration due to gravity (f/sec^2)


# Euler angle to fixed frame coordinate mapping - Rocket convention Euler mapping
def euler_psi(psi_last,phi_last,theta_last,omega_x,omega_y,omega_z,delta_t):
    psi = (sin(phi_last)/sin(theta_last) * omega_x + cos(phi_last)/sin(theta_last) * omega_y) * delta_t + psi_last
    return psi
def euler_phi(psi_last,phi_last,theta_last,omega_x,omega_y,omega_z,delta_t):
    phi = (-sin(phi_last)*cos(theta_last)/sin(theta_last) * omega_x  - cos(phi_last)*cos(theta_last)/sin(theta_last) * omega_y + omega_z) * delta_t + phi_last
    return phi
def euler_theta(psi_last,phi_last,theta_last,omega_x,omega_y,omega_z,delta_t):
    theta = (cos(phi_last) * omega_x - sin(phi_last) * omega_y) * delta_t + theta_last
    return theta


def eulerX(x,y,z,phi,psi,theta):
    X = (cos(phi)*cos(psi) - sin(phi)*cos(theta)*sin(psi))*x + (-sin(phi)*cos(psi)-sin(psi)*cos(theta)*cos(phi))*y + (sin(theta)*sin(psi))*z
    return X
def eulerY(x,y,z,phi,psi,theta):
    Y = (cos(phi)*sin(psi) + sin(phi)*cos(theta)*cos(psi))*x + (-sin(phi)*sin(psi)+cos(phi)*cos(theta)*cos(psi))*y + (-sin(theta)*cos(psi))*z
    return Y
def eulerZ(x,y,z,phi,psi,theta):
    Z = (sin(theta)*sin(phi))*x + (sin(theta)*cos(phi))*y + cos(theta)*z
    return Z


def eulerx(X,Y,Z,phi,psi,theta):
    x = (cos(phi)*cos(psi)-sin(phi)*cos(theta)*sin(psi))*X + (cos(phi)*sin(psi)+sin(phi)*cos(theta)*cos(psi))*Y + (sin(phi)*sin(theta))*Z
    return x
def eulery(X,Y,Z,phi,psi,theta):
    y = (-sin(phi)*cos(psi)-cos(phi)*cos(theta)*sin(psi))*X + (-sin(phi)*sin(psi)+cos(phi)*cos(theta)*cos(psi))*Y + (cos(phi)*sin(theta))*Z
    return y
def eulerz(X,Y,Z,phi,psi,theta):
    z = (sin(theta)*sin(psi))*X + (-sin(theta)*cos(psi))*Y + (cos(theta))*Z
    return z


def Theta(X,Y,Z):
    if X+Y+Z == 0:
        Theta = 0
    else:
        if Z < 0:
            Theta = -asin(((X**2+Y**2)**.5)/((X**2+Y**2+Z**2)**.5))+ pi
        else:
            Theta = asin(((X**2+Y**2)**.5)/((X**2+Y**2+Z**2)**.5))
    return Theta   


def Smooth(x,m):
    n = len(x)
    y = [0 for i in range(n)]
    for i in range((m-1)/2,n-(m-1)/2):
        for j in range(i-(m-1)/2,i+(m-1)/2):
            y[i] = y[i]+x[j]
        y[i] = y[i]/m
    for i in range(0,(m-1)/2):                   
        y[i] = y[(m-1)/2]
    for i in range(n-(m-1)/2,n):
        y[i] = y[n-(m-1)/2-1]
    return y

 
