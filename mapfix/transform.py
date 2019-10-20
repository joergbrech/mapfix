#!/usr/bin/env python
# -*- coding: iso-8859-1 -*- 

import numpy as np
import math

import re

from pyproj import Proj

import mapfix.helper as h

class projection:
    
    proj4         = None         #The Pyproj class for the projection
    projectionKey = None         #The key of the current projection 
    description   = ""           #A more descriptive name than the key
    projparams    = None         #pyproj parameters for Proj.__new__
    
    def __init__(self,projkey,description,projparams):
        self.projectionKey=projkey
        self.description=description
        self.projparams=projparams
        self.proj4 = Proj(projparams)
    
    def update_from_coordinates(self,cs,store):
        """
        update projection parameters based on a set of coordinates. Only used
        if the key is TMERC-MC or UTM-MC
        """
        
        if self.projectionKey=="TMERC-MC":
            #if marker-centered transverse mercator, calc center longitude and reinit proj4
            center_lon = np.mean(cs[0::2])
            center_lat = np.mean(cs[1::2])
            self.projparams["lat_0"] = center_lat
            self.projparams["lon_0"] = center_lon
            
        elif self.projectionKey=="UTM-MC":
            #if marker-centered UTM, calc zone from  center longitude and reinit proj4
            center_lon = np.mean(cs[0::2])
            center_lat = np.mean(cs[1::2])
            e=self.projparams['ellps']
            d=self.projparams['datum']
            self.projparams,zoneName = self.utm_zone(center_lat,center_lon,ellps=e,datum=d)
            self.description = "UTM (local), Zone {}".format(zoneName)
        else:
            return
            
        self.proj4 = Proj(self.projparams)
        store.put('projection',
                projkey=self.projectionKey,
                description=self.description,
                projparams=self.projparams
                )
        
    def utm_zone(self,lat,lon,ellps='WGS84',datum='WGS84'):
        """
        calculates the UTM zone of lat lon and returns a tupel containing
        the projparams of the UTM zone and the zone name
        
        lat lon must be in degrees (not radians)
        negative lat for Southern hemisphere
        negative lon for Eastern hemisphere
        
        """
    
        if lat<0:
            south=True
            hemisphere_str = ' +south'
        else:
            south=False
            hemisphere_str = ''
        
        #shift longitutes from [-180,180] to [0,360]
        lon += 180
        
        #handle special cases first
        if lat<=-80:
            #check for antarctic zones
            if lon<=180:
                zoneName = "A"
            else:
                zoneName = "B"
            projparams = {"proj":"stere","lat_0":-90,"lat_ts":-90,"lon_0":0,"k":0.994,"x_0":2000000,"y_0":2000000,"ellps":ellps,"datum":datum,"units":"m","no_defs":True}
            return projparams,zoneName
        elif lat>84:
            #check for arctic zones
            if lon<=180:
                zoneName = "Y"
            else:
                zoneName = "Z"
            projparams = {"proj":"stere","lat_0":90,"lat_ts":90,"lon_0":0,"k":0.994,"x_0":2000000,"y_0":2000000,"ellps":ellps,"datum":datum,"units":"m","no_defs":True}
            return projparams,zoneName
        elif lat>72 and lat<=84:
            #check for the special zones of Spitzbergen
            zoneLetter="X"
            if lon>6*(31-1) and lon<=6*(31-1)+9:
                zoneNumber = "31"
            elif lon>6*(31-1)+9 and lon<=6*(31-1)+21:
                zoneNumber = "33"
            elif lon>6*(31-1)+21 and lon<=6*(31-1)+33:
                zoneNumber = "35"
            elif lon>6*(31-1)+33 and lon<=6*(31-1)+42:
                zoneNumber = "37"
        elif lat>56 and lat<=64:
            #check for the special zones of southern Norway
            zoneLetter="V"
            if lon>6*(31-1) and lon<=6*(31-1)+3:
                zoneNumber = "31"
            elif lon>6*(31-1)+3 and lon<=6*(31-1)+9:
                zoneNumber = "32"
        else:
            #no more special cases!
            zoneNumber = int(math.ceil(lon/6.))
            latitudinal_zoneNumber = int((lat+80)/8.)
            #alphabet from C-X, without the letters I and O
            zoneLetter = "CDEFGHJKLMNPQRSTUVWX"[latitudinal_zoneNumber]
            
        zoneName = "{}{}".format(zoneNumber,zoneLetter)
        projparams = {"proj":"utm","zone":zoneNumber,"south":south,"ellps":ellps,"datum":datum,"units":"m","no_defs":True}
        return projparams,zoneName
    
    def unit_string(self):
        """
        get the units used in the current projection from the proj4 class
        """
        defstr = self.proj4.definition_string()
        
        #first, check if the projection is latlon. 
        match = re.search(r"(proj=longlat)",defstr)
        if match:
            return "°"
        
        #next, check if the units are specified
        match = re.search(r"units=(\w*)", defstr)
        if match:
            result = match.group(1)
        else:
            result = ""
        return result
        
    
    
    def proj(self,X,inverse = False):
        n = int(0.5*len(X))
        x,y = self.proj4(X[0::2],X[1::2],inverse=inverse)
        #return np.reshape(np.concatenate((x,y),axis=1),(2*n,1))
        xy = np.zeros(2*n)
        for i in range(n):
            xy[2*i  ] = x[i]
            xy[2*i+1] = y[i]
        return xy
        
    def projInv(self,X):
        return self.proj(X,inverse=True)
        

class homography: 
    
    # parameters for the calibration
    maxiter             = 100       # max. number of Gauss-Newton iterations
    atol                = 1e-8      # absolute tolerance
    rtol                = 1e-3     # relative tolerance
    retry_w_lower_level = True      # retry calibration with lower level after fail
    
    #TODO haven't changed these. Delete?
    rtol_lsq_only       = True      # Only do rtol check for least squares
    prescale            = True      # scale input markers to unit square to 
                                    # avoid badly scaled Jacobians
    solve_normal_eqs    = False     # solve normal equations (J.TJ)^{-1}*J.Tr
    relax               = 1         # use underrelaxation
    levenberg_marquardt = False     # use Levenberg Marquardt (LM) algorithm
    relax_lm            = 1e-1      # constant relaxation factor for LM
    focal_before_affine = False     # determine p4 and p5 in level 1 rather     
                                    # than p1 and p3
    
    #TODO dimension = 3 not supported yet
    dimension           = 2         # map is aerial view => 3 (normal case is 2D)
    
    calibration_info = {}
    
    #parameters for the homography
    H     = np.zeros((3,4))
    H[0,0]=H[1,1]=H[2,2]=H[2,3]=1
    H_inv = H
    
    def x2d(self,X,H=None):
        
        # project map point X to screen point d
        
        if H is None:
            H=self.H
        
        k = self.dimension
        #TODO try if len(X) is multiple of k
        n = int(len(X)/k)
        d = np.zeros(2*n)
        for i in range(n):
            d[2*i:2*(i+1)] = self.map(X[k*i:k*(i+1)],H)
        return d

    
    def d2x(self,d,H=None):
        
        # project screen point d to map point X
        
        if H is None:
            H_inv = self.H_inv
        else:
            H_inv = self.inverse(H)

        return self.x2d(d,H_inv)
    
    def calibrate(self,ds,Xs,level=2):
        
        # calibrate parameters for the homotopy using Gauss-Newton algorithm with calibration markers (i.e. (d,X)-pairings )
        
        
        returncode = -1     #return code
                            #  -1 : something went wrong
                            #   0 : no convergence before maxiter reached
                            #   1 : not enough markers
                            #   2 : convergence, residual below relative tolerance
                            #   3 : convergence, residual below absolute tolerance
                            #   4 : error in linear solve
        
        k = self.dimension
        n = int(len(Xs)/k) # number of markers
        
        # at least two markers are needed (ds.size = 4)
        if n < 2:
            returncode = 1
            return returncode
        
        # least squares if there are more markers than level+2
        lsq = (n - level - 2 > 0)
        
        # get current unscaled inverse residual
        r = self.d2x(ds) - Xs
        #r = ds - self.x2d(Xs)
        res_pre = r.dot(r)/n
        
        level = max(level,0)
        level = min(level,n-2)
                    #level depends on number of markers
                    #
                    #  level==0, 2 markers           -> euclidean + scale
                    #  level==1, 3 markers           -> affine
                    #  level==2, 4 markers or more   -> homography
        
        # functions to calculate parameters from variables, and Jacobians are
        # different on each level
        if level==0:
            def param2var(H):
                #                     0      1      2      3
                return np.array([H[0,0],H[1,0],H[0,3],H[1,3]])
            def var2param(P):
                return np.array([[P[0],-P[1],0,P[2]],
                                 [P[1], P[0],0,P[3]],
                                 [   0,    0,1,   1]])
            def Jacobian(x,d):
                #TODO update via name binding, do not allocate every iteration
                J = np.zeros((x.size,4))
                for i in range(n):
                    X1 = x[k*i  ]
                    X2 = x[k*i+1]
                    J[2*i  ,:] = np.array([X1, -X2, 1, 0])
                    J[2*i+1,:] = np.array([X2,  X1, 0, 1])
                return J
        elif level==1:
            if self.focal_before_affine:
                def param2var(H):
                    #                     0      1      2      3      4      5
                    return np.array([H[0,0],H[1,0],H[0,3],H[1,3],H[2,0],H[2,1]])
                def var2param(P):
                    return np.array([[P[0],-P[1],0,P[2]],
                                     [P[1], P[0],0,P[3]],
                                     [P[4], P[5],1,   1]])
                def Jacobian(x,d):
                    J = np.zeros((x.size,6))
                    for i in range(n):
                        X1 = x[k*i  ]
                        X2 = x[k*i+1]
                        J[2*i  ,:] = np.array([X1, -X2, 1, 0, -d[2*i  ]*X1, -d[2*i  ]*X2])
                        J[2*i+1,:] = np.array([X2,  X1, 0, 1, -d[2*i+1]*X1, -d[2*i+1]*X2])
                    return J
            else:
                def param2var(p):
                    #                     0      1      2      3      4      5
                    return np.array([H[0,0],H[1,0],H[0,3],H[1,3],H[0,1],H[1,1]])
                def var2param(P):
                    return np.array([[P[0], P[4],0,P[2]],
                                     [P[1], P[5],0,P[3]],
                                     [   0,    0,1,   1]])
                def Jacobian(x,d):
                    J = np.zeros((x.size,6))
                    for i in range(n):
                        X1 = x[k*i  ]
                        X2 = x[k*i+1]
                        J[2*i  ,:] = np.array([X1,  0, 1, 0, X2, 0 ])
                        J[2*i+1,:] = np.array([ 0, X1, 0, 1,  0, X2])
                    return J
        else: # level == 2
            def param2var(p):
                #                     0      1      2      3      4      5      6      7
                return np.array([H[0,0],H[0,1],H[1,0],H[1,1],H[2,0],H[2,1],H[0,3],H[1,3]])
            def var2param(P):
                return np.array([[P[0], P[1],0,P[6]],
                                 [P[2], P[3],0,P[7]],
                                 [P[4], P[5],1,   1]])
            def Jacobian(x,d):
                J = np.zeros((x.size,8))
                for i in range(n):
                    X1 = x[k*i  ]
                    X2 = x[k*i+1]
                    J[2*i  ,:] = np.array([X1, X2,  0,  0, -d[2*i  ]*X1, -d[2*i  ]*X2, 1, 0])
                    J[2*i+1,:] = np.array([ 0,  0, X1, X2, -d[2*i+1]*X1, -d[2*i+1]*X2, 0, 1])
                return J
               
        #get initial guess for unknowns P from self.p
        H = np.array(self.H,copy=True)  
        
        if self.prescale and level>0:
           
            x,SX,SXinv = self.scale2unitsquare(Xs,self.dimension,fake3D=True)
            d,SD,SDinv = self.scale2unitsquare(ds,2)
              
            H = SD.dot(H).dot(SXinv)
            H=H/H[2,3]
            
            def calc_res(r):                
                rscale = self.homogeneous_transform(r,SDinv,2,affine=False)
                return rscale.dot(rscale)/n
        else:
            x = Xs
            d = ds
            def calc_res(r):
                return r.dot(r)/n
        
        P=param2var(H)
            
        ##initialize Jacobians to zero 
        #if level==0:
            #J = np.zeros((x.size,4))
        #elif level==1:
            #J = np.zeros((x.size,6))
        #else:
            #J = np.zeros((x.size,8))
        
        # main iteration loop
        iter = 0
        res_abs = 1e6
        res_rel = 1e6
        converged = False
        while iter < self.maxiter:
            
            
            #calculate residual
            d_calc = self.x2d(x,H)
            r = d - d_calc
            
            # remember this for convergence check AFTER iteration
            res_abs_prev = res_abs
            
            #first convergence check (absolute)
            res_abs = calc_res(r)      
            if res_abs < self.atol:
                returncode = 3
                converged = True
                break;
            
                
            J = Jacobian(x,d_calc)
            
            if lsq or self.solve_normal_eqs:
                b = np.dot(J.T,r)
                A = np.dot(J.T,J)
            else:
                b = r
                A = J
                
            if self.levenberg_marquardt:
                A += self.relax_lm*np.diag(np.diag(A))
            
            # The actual Gauss-Newton iteration
            try:
                #first, try LU decomposition
                DP = np.linalg.solve(A,b)
            except np.linalg.linalg.LinAlgError:
                print(" ***** Linear Solver error")
                returncode = 4
                converged = False
                break
            
            # second convergence check (relative)
            res_rel = abs((res_abs-res_abs_prev)/max(res_abs_prev,1e-10))
            res_rel = max(res_rel,abs(DP.dot(DP)/max(P.dot(P),1e-10)))
            if (res_rel < self.rtol) and not (self.rtol_lsq_only and not lsq):
                returncode = 2
                converged = True
                break;
            
            P += self.relax*DP
            H = var2param(P)                
            
            # go to next iteration
            iter+=1
        
        if converged:
            
            if self.prescale and level>0:
                H = SDinv.dot(H).dot(SX)
                H=H/H[2,3]
                
            #CONVERGENCE DOESN'T MEAN THE HOMOGRAPHY IS GOOD
                
            #check if the absolute residual improved or if the homography is degenerate (TODO, how to identify degenerate cases?)
            #r = ds - self.x2d(Xs,H)
            r = self.d2x(ds,H) - Xs
            res_post = r.dot(r)/n
            if res_post >= 2*res_pre:
                print("Calibration converged in {} iteratons, but the absolute residual did not improve. res_pre = {} res_post = {}".format(iter,res_pre,res_post))
                converged = False
            else:
                self.calibration_info['res_pre'    ] = math.sqrt(res_pre)
                self.calibration_info['res_post'   ] = math.sqrt(res_post)
                self.calibration_info['num_iter'   ] = iter
                self.calibration_info['num_markers'] = n
                self.calibration_info['level'      ] = level
                self.calibration_info['time'       ] = h.now_string(seconds=True)
                self.calibration_info['conv_code'  ] = returncode
                
                self.H     = np.array(H,copy=True)
                self.H_inv = self.inverse()
                
                print("converged in {} iterations.\n   res (abs) = {}\n   res (rel) = {}".format(iter,res_abs,res_rel))
        else:
            print("no convergence in {} iterations.\n   res (abs) = {}\n   res (rel) = {}".format(iter,res_abs,res_rel))
            returncode = 0
        
        if not converged and self.retry_w_lower_level:
            
            # retry the calibration with lower level
            if level > 0:
                print("Falling back to Level {}".format(level-1))
                returncode = self.calibrate(ds,Xs,level-1)
                #if 'num_iter' in self.calibration_info:
                    #self.calibration_info['num_iter'] += iter
                #else:
                    #self.calibration_info['num_iter'] = iter
        
        return returncode
    
    # =============== internal functions =============== #
   
    def map(self,X,H):
        if len(X)==2:
            X=np.hstack((X,[0,1]))
        elif len(X)==3:
            X=np.hstack((X,[1]))
        d = H.dot(X)
        d[0]/=d[2]
        d[1]/=d[2]
        #TODO try for zero in divide, X wrong length
        return d[0:2]
    
    def scale2unitsquare(self,y,k=2,fake3D=False):
        
        # three cases: 
        # 1) y is 2D  =>  k=2, fake3D=False
        # 2) y is 3D  =>  k=3, fake3D=False
        # 2) y is 2D but requires a fake 3 component in S to 
        #    properly scale H from the right
        #             =>  k=2, fake3D=True
        
        
        # k is dimension of vectors in flattend y
        n = int(len(y)/k)
        
        l=k
        if k==2 and fake3D:
            k=3
        
        dx=np.zeros(k)
        bx=np.zeros((k,1))
        for i in range(k):
            if i==2 and fake3D:
                dx[i]=1
                bx[i]=0
            else:
                xmin=np.min(y[i::l])
                xmax=np.max(y[i::l])
                dx[i] = xmax - xmin
                bx[i] =-xmin/dx[i]-0.5
        
        S = np.diag(1/dx)
        S = np.hstack((S,bx))
        S = np.vstack((S,np.zeros(k+1)))
        S[k,k]=1
        
        Sinv = np.diag(dx)
        Sinv = np.hstack((Sinv,-Sinv.dot(bx)))
        Sinv = np.vstack((Sinv,np.zeros(k+1)))
        Sinv[k,k]=1
        
            
        x = self.homogeneous_transform(y,S,l)
        
        return x,S,Sinv
    
    def homogeneous_transform(self,y,S,k=2,affine=True):
        
        x = np.zeros(len(y))
        l= S.shape[0]-1
        n = int(len(y)/k)
        for i in range(n):
            x[k*i:k*(i+1)] = S[0:k,0:k].dot(y[k*i:k*(i+1)]) + affine*S[0:k,l]
        return x

    def inverse(self,H=None):
        
        if H is None:
            H=self.H
            
        F = np.zeros((3,4))
        denom   =   H[0,0]*H[1,1] - H[1,0]*H[0,1]
        F[0,0]  =          H[1,1] - H[2,1]*H[1,3]
        F[0,1]  = -        H[0,1] + H[2,1]*H[0,3]
        F[1,0]  = -        H[1,0] + H[2,0]*H[1,3]
        F[1,1]  =          H[0,0] - H[2,0]*H[0,3]
        F[2,0]  =   H[1,0]*H[2,1] - H[2,0]*H[1,1]
        F[2,1]  = - H[0,0]*H[2,1] + H[0,1]*H[2,0]
        F[0,3]  = - H[1,1]*H[0,3] + H[0,1]*H[1,3]
        F[1,3]  =   H[1,0]*H[0,3] - H[0,0]*H[1,3]
        F/=denom
        F[2,2]=1
        F[2,3]=1
        return F
    
