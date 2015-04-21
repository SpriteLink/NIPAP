package net.spritelink.nsonipap;

import net.spritelink.nsonipap.namespaces.*;

import java.util.*;
import java.math.BigInteger;

import org.apache.log4j.Logger;

import com.tailf.conf.*;
import com.tailf.ncs.ApplicationComponent;
import com.tailf.cdb.*;
import com.tailf.maapi.*;
import com.tailf.ncs.annotations.*;
import com.tailf.navu.*;
import com.tailf.ncs.ns.Ncs;

import java.net.SocketException;
import java.net.InetAddress;
import java.net.URL;
import java.util.ArrayList;
import java.util.EnumSet;

import jnipap.*;

public class ConfigCdbSub implements ApplicationComponent {
    private static Logger LOGGER = Logger.getLogger(ConfigCdbSub.class);

    private CdbSubscription sub = null;
    private CdbSession wsess;
    private CdbSession rsess;

    public ConfigCdbSub() {
    }

    @Resource(type=ResourceType.CDB, scope=Scope.CONTEXT,
            qualifier="reactive-fm-loop-subscriber")
    private Cdb cdb;

    @Resource(type=ResourceType.CDB, scope=Scope.CONTEXT,
            qualifier="w-reactive-fm-loop")
    private Cdb wcdb;

    @Resource(type=ResourceType.MAAPI, scope=Scope.INSTANCE,
            qualifier="reactive-fm-m")
    private Maapi maapi;

	private int th = -1;
	private NavuContainer ncsRoot;
	private NavuContainer operRoot;

	private Connection nipapCon;

    public void init() {
        LOGGER.info("Starting the CDB Connection...");
        try {
            wsess = wcdb.startSession(CdbDBType.CDB_OPERATIONAL);
            //Start CDB session
            maapi.startUserSession("admin", InetAddress.getLocalHost(),"system",
                    new String[] {"admin"},
                    MaapiUserSessionFlag.PROTO_TCP);

			th = maapi.startTrans(Conf.DB_RUNNING, Conf.MODE_READ);
			NavuContainer root = new NavuContainer(new NavuContext(maapi, th));
			ncsRoot = root.container(Ncs.hash);
			NavuContainer cdbRoot = new NavuContainer(new NavuContext(cdb));
			NavuContainer operRoot = cdbRoot.container(Ncs.hash);

            sub = cdb.newSubscription();
            sub.subscribe(1, new nipap(), "/services/nipap/pool/request");
            // Tell CDB we are ready for notifications
            sub.subscribeDone();

            // Setup the external allocator
            //externalAllocator.initialize();

        }
        catch (Exception e) {
            LOGGER.error("", e);
        }
    }

    public void run() {
        LOGGER.info("Starting the CDB subscriber...");        
        try {

            while(true) {
                // Read the subscription socket for new events
                int[] points = null;
                try {
                    // Blocking call, will throw an exception on package reload/redeploy
                    points = sub.read();
                } catch (ConfException e) {
                    LOGGER.debug("Possible redeploy/reload of package, exiting");
                    return;
                }
                // DiffIterateFlags tell our DiffIterator implementation what values we want
                EnumSet<DiffIterateFlags> enumSet =
                        EnumSet.<DiffIterateFlags>of(
                                DiffIterateFlags.ITER_WANT_PREV,
                                DiffIterateFlags.ITER_WANT_ANCESTOR_DELETE,
                                DiffIterateFlags.ITER_WANT_SCHEMA_ORDER);
                ArrayList<Request> reqs = new ArrayList<Request>();
                try {
                    // Iterate through the diff tree using the Iter class
                    // reqs ArrayList is filled with requests for operations (create, delete)
                    sub.diffIterate(points[0],
                            new Iter(sub),
                            enumSet, reqs);
                }
                catch (Exception e) {
                    reqs = null;
                }

                // Loop through CREATE or DELETE requests
                for (Request req : reqs) {
                    LOGGER.debug("Requested NIPAP action, op=" + req.op + " , type=" + req.t);

					try {
						// TODO: make backend configurable (now it is 'default')
						ConfValue bHost = maapi.getElem(th, "/services/nipap/backend{default}/hostname");
						ConfValue bPort = maapi.getElem(th, "/services/nipap/backend{default}/port");
						ConfValue bUser = maapi.getElem(th, "/services/nipap/backend{default}/username");
						ConfValue bPass = maapi.getElem(th, "/services/nipap/backend{default}/password");

						URL url = new URL("http://" + String.valueOf(bHost) + ":" + String.valueOf(bPort) + "/RPC2");
						nipapCon = new Connection(url, String.valueOf(bUser), String.valueOf(bPass));
						nipapCon.authoritative_source = "ncs";

					} catch (Exception e) {
						LOGGER.error("Unable to initiate connection to NIPAP");
					}


					// allocate integer
                    if ((req.op == Operation.ALLOCATE) &&
                            (req.t == Type.Prefix)) {

						LOGGER.info("Trying to allocate a prefix for: " + req.request_key + " from pool: " + req.pool_key);
						String poolName = String.valueOf(req.pool_key).replaceAll("[{}]", "");

						Prefix p = new Prefix();
						// get pool for
						try {
							HashMap poolSpec = new HashMap();
							poolSpec.put("name", poolName);
							List poolRes = Pool.list(nipapCon, poolSpec);

							// options, like address-family
							AddPrefixOptions opts = new AddPrefixOptions();
							ConfEnumeration family = (ConfEnumeration)maapi.getElem(th, req.path + "/family");
							opts.put("family", family.getOrdinalValue());

							ConfValue rDescription = maapi.getElem(th, req.path + "/description");
							if (rDescription != null)
								p.description = String.valueOf(rDescription);

							ConfValue rNode = maapi.getElem(th, req.path + "/node");
							if (rNode != null)
								p.node = String.valueOf(rNode);

							p.save(nipapCon, (Pool)poolRes.get(0), opts);

						} catch (Exception e) {
							LOGGER.error("Unable to get prefix from NIPAP", e);
						}

                        // Write the result
						if (p.family == 4) {
							ConfIPv4Prefix prefixValue = new ConfIPv4Prefix(p.prefix);
							LOGGER.info("SET: " + req.path + "/prefix -> " + prefixValue);
							wsess.setElem(prefixValue, req.path + "/prefix");
						} else if (p.family == 6) {
							ConfIPv6Prefix prefixValue = new ConfIPv6Prefix(p.prefix);
							LOGGER.info("SET: " + req.path + "/prefix -> " + prefixValue);
							wsess.setElem(prefixValue, req.path + "/prefix");
						}
						ConfUInt64 prefixIdValue = new ConfUInt64(p.id);
						wsess.setElem(prefixIdValue, req.path + "/prefix_id");

						// Redeploy
						try {
							ConfValue redeployPath = maapi.getElem(th, req.path + "/redeploy-service");
							LOGGER.info("redeploy-service: " + redeployPath);
							redeploy(maapi, redeployPath + "/re-deploy");
						} catch (Exception e) {
						}
                    }

                    else if (req.op == Operation.DEALLOCATE &&
                            (req.t == Type.Prefix)) {
                        //Deallocate prefix

                        try {
                            ConfUInt64 p_id = (ConfUInt64)wsess.getElem(req.path + "/prefix_id");
							LOGGER.info("Removing prefix ID: " + p_id);
							Prefix p = Prefix.get(nipapCon, Integer.parseInt(String.valueOf(p_id)));
							p.remove(nipapCon);
							wsess.delete(req.path + "/prefix_id");
							wsess.delete(req.path + "/prefix");
                        } catch (Exception e) {
                            LOGGER.error("Unable to remove prefix from NIPAP",e);
                        }

                    }

                }

                // Tell the subscription we are done 
                sub.sync(CdbSubscriptionSyncType.DONE_PRIORITY);
            }
        }
        catch (SocketException e) {
            // silence here, normal close (redeploy/reload package)
        }
        catch (Exception e) {
            LOGGER.error("",e );
        }
    }

    public void finish() {
        safeclose(cdb);
        safeclose(wcdb);
        try {
            maapi.getSocket().close();
        }
        catch (Exception e) {
        }
    }


    private void safeclose(Cdb s) {
        try {s.close();}
        catch (Exception ignore) {}
    }


    private enum Operation { ALLOCATE, DEALLOCATE }
    private enum Type { Prefix }

    private class Request {
        Operation op;
        Type t;
        ConfPath path;
		ConfKey pool_key;
        ConfKey request_key;
    }

    private class Iter implements CdbDiffIterate {
        CdbSubscription cdbSub;

        Iter(CdbSubscription sub ) {
            this.cdbSub = sub;
        }

        public DiffIterateResultFlag iterate(
                ConfObject[] kp,
                DiffIterateOperFlag op,
                ConfObject oldValue,
                ConfObject newValue, Object initstate) {     

            @SuppressWarnings("unchecked")
            ArrayList<Request> reqs = (ArrayList<Request>) initstate;

            try {
                ConfPath p = new ConfPath(kp);
                LOGGER.info("ITER " + op + " " + p);
                // The kp array contains the keypath to the ConfObject in reverse order, for example:
                // /ncs:services/nipap:nipap/prefix{bar} -> ["{bar}", "nipap:prefix", "nipap:nipap", "ncs:services" ]
                // Since we are subscribing to the changes on /ncs:services/ura:ura, the 3rd node from the end of the list always contains the service name (list key)
                Request r = new Request();
                r.path = p;
				if (kp[1].toString().equals("nipap:request")) {
					r.request_key = (ConfKey)kp[0];
					if (kp[3].toString().equals("nipap:pool")) {
						r.t = Type.Prefix;
						r.pool_key = (ConfKey)kp[2];
					}
					if (op == DiffIterateOperFlag.MOP_CREATED) {
						r.op = Operation.ALLOCATE;
						reqs.add(r);
					} else if (op == DiffIterateOperFlag.MOP_DELETED) {
						r.op = Operation.DEALLOCATE;
						reqs.add(r);
					}
				}
            }
            catch (Exception e) {
                LOGGER.error("", e);
            }
            return DiffIterateResultFlag.ITER_RECURSE;

        } 
    }



    // redeploy MUST be done in another thread, if not system
    // hangs, since the CDB subscriber cannot do its work
    private void redeploy(Maapi m, String path) {
        Redeployer r = new Redeployer(m, path);
        Thread t = new Thread(r);
        t.start();
    }

    private class Redeployer implements Runnable {
        private String path;
        private Maapi m;

        public Redeployer(Maapi m, String path) {
            this.path = path; this.m = m;
        }

        public void run() {
            try {
                m.requestAction(new ConfXMLParam[] {},
                        path);
            } catch (Exception e) {
                LOGGER.error("error in re-deploy", e);
                throw new RuntimeException("error in re-deploy", e);
            }
        }
    }
}
