package com.example.movieactors.actor;

import java.util.List;

public interface ActorsDao {
    List<Actor> selectActors();
    int insertActor(Actor actor);
}
